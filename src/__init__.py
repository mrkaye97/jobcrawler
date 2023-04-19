from flask import Flask
from config import Config
from apscheduler.schedulers.background import BackgroundScheduler
from flask_migrate import Migrate
import os
from .models import *
from .jobs import *
from flask_login import LoginManager

sched = BackgroundScheduler()

app = Flask(__name__)
app.secret_key = os.urandom(24)

from src import routes

app.config.from_object(Config)
migrate = Migrate(app, db)
db.init_app(app)
migrate.init_app(app, db)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return Users.query.get(int(user_id))

@sched.scheduled_job(trigger = 'interval', hours = 3, id='crawl')
def crawl():
    """ Function for test purposes. """
    print("Scheduler is alive!")
    results = []

    with app.app_context():
        searches = Searches.\
                query.\
                join(Companies).\
                with_entities(Searches.id.label("search_id"), Companies.id.label("company_id"), Companies.name, Companies.board_url, Searches.search_text, Companies.scraping_method).\
                all()

        for search in searches:
            if search.scraping_method == 'selenium':
                results = results + get_links_selenium(url = search.board_url, query = search.search_text, company = search.name)
            elif search.scraping_method == 'soup':
                results = results + get_links_soup(url = search.board_url, query = search.search_text, company = search.name)
            else:
                results = []

    result_txt = "\n".join(results)

    if os.environ.get("SEND_EMAIL") == "yes":
        send_email(
            sender_email = "mrkaye97@gmail.com",
            sender_name = "Matt Kaye",
            recipient = "matt.kaye@collegevine.com",
            subject = "Your daily job feed digest",
            body = f"""
                Here are your links for the day!

                {result_txt}
            """
        )
    else:
        print(result_txt)

sched.start()
