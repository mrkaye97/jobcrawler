from flask import Flask
from config import Config
from apscheduler.schedulers.background import BackgroundScheduler
from flask_migrate import Migrate
import os
from .models import *
from .jobs import crawl_for_postings, run_email_send_job
from flask_login import LoginManager
import logging
import sys
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sched = BackgroundScheduler()

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    integrations=[
        FlaskIntegration(),
    ],

    traces_sample_rate=1.0
)

app = Flask(__name__)
app.secret_key = os.urandom(24)

root = logging.getLogger()
root.setLevel(logging.INFO)

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
    return Users.query.get(int(user_id))

@sched.scheduled_job(trigger = 'cron', hour = 23, id = 'crawl')
def crawl():
    app.logger.info("Kicking off scraping job")
    crawl_for_postings(app, db)

@sched.scheduled_job(trigger = "cron", hour = 0, id = "send_emails")
def send_emails():
    app.logger.info("Kicking off email sending job")
    run_email_send_job(app)

sched.start()
