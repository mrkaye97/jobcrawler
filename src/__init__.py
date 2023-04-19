from flask import Flask
from config import Config
from apscheduler.schedulers.background import BackgroundScheduler
from flask_migrate import Migrate
import os
from .models import *
from .jobs import *

sched = BackgroundScheduler()

app = Flask(__name__)

from src import routes

app.config.from_object(Config)
migrate = Migrate(app, db)
db.init_app(app)
migrate.init_app(app, db)

@sched.scheduled_job(trigger = 'interval', hours = 3, id='crawl')
def crawl():
    """ Function for test purposes. """
    print("Scheduler is alive!")
    results = []

    with app.app_context():
        searches = db.session.query.join(Companies).with_entities(Companies.name, Companies.board_url, Searches.search_text)

        for search in searches:
            if search.company in ['Headspace', 'Spotify']:
                results = results + get_links_selenium(url = search.board_url, query = search.search_text, company = search.name)
            else:
                results = results + get_links_soup(url = search.board_url, query = search.search_text, company = search.name)

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
