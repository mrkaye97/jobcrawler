from flask import Flask
from config import Config
from apscheduler.schedulers.background import BackgroundScheduler
from flask_migrate import Migrate
import os
from .models import *
from .jobs import *
from flask_login import LoginManager
import logging
import datetime
from urllib.parse import urljoin

sched = BackgroundScheduler()

app = Flask(__name__)
app.secret_key = os.urandom(24)

from src import routes

app.config.from_object(Config)
migrate = Migrate(app, db)
db.init_app(app)
migrate.init_app(app, db)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return Users.query.get(int(user_id))

@sched.scheduled_job(trigger = 'interval', hours = 3, id = 'crawl')
def crawl():
    app.logger.info("Kicking off scraping job")
    with app.app_context():
        for company in Companies.query.all():
            app.logger.info(f"Scraping {company.name}'s job board")
            if company.scraping_method == 'selenium':
                links = get_links_selenium(url = company.board_url)
            elif company.scraping_method == 'soup':
                links = get_links_soup(url = company.board_url)
            else:
                links = []

            app.logger.info(f"Finished scraping {company.name}'s job board")
            app.logger.info(f"Removing existing links for {company.name}")

            existing_postings = Postings.query.get(company.id)
            db.session.delete(existing_postings)

            app.logger.info(f"Finished removing existing links for {company.name}")
            app.logger.info(f"Adding new links for {company.name}")

            for link in links:
                new_posting = Postings(company_id = company.id, link_text = link["text"], link_href = link["href"])
                db.session.add(new_posting)

            app.logger.info("Committing changes.")
            db.session.commit()

@sched.scheduled_job(trigger = "interval", hours = 24, id = "send_emails")
def send_emails():
    app.logger.info("Kicking off email sending job")
    with app.app_context():
        user_email_frequencies = 7
        current_day = (datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).days

        for user in Users.query.all():
            ## TODO: Replace `user_email_frequencies` with the frequency of
            ## the individual user
            Searches.\
                query.\
                join(Companies).\
                with_entities(Searches.id.label("search_id"), Companies.id.label("company_id"), Companies.name, Companies.board_url, Searches.search_text, Companies.scraping_method).\
                all()

            if current_day % user_email_frequencies == 0:
                user_search_results = Searches.\
                    query.\
                    filter_by(user_id = user.id).\
                    join(Companies).\
                    join(Postings).\
                    join(Users).\
                    with_entities(
                        Users.email,
                        Users.first_name,
                        Companies.name.label("company_name"),
                        Searches.search_text,
                        Postings.link_href,
                        Postings.link_text,
                    ).\
                    all()

                matching_postings = [f"{search.link_text} @ {search.company_name}: {search.link_href}" for search in user_search_results if search.search_text in search.link_text]
                link_text = "\n".join(matching_postings)

                message = f"""
                    Hey {user_search_results.name},

                    Here are your links for the day!

                    {link_text}

                    Have a good one! I'll send you another round of matching links in {user_email_frequencies} days.

                    Matt
                """

                if os.environ.get("ENV") == "PROD":
                    send_email(
                        sender_email = "mrkaye97@gmail.com",
                        sender_name = "Matt Kaye",
                        recipient = user_search_results.email,
                        subject = "Your daily job feed digest",
                        body = message
                    )
                else:
                    app.logger.info(message)

sched.start()
