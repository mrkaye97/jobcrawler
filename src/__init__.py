## Flask
from flask import Flask
from flask_admin import Admin
from flask_admin.menu import MenuLink
from flask_admin.contrib.sqla import ModelView
from config import Config
from apscheduler.schedulers.background import BackgroundScheduler
from flask_migrate import Migrate

## Application
from src.models import db
from src.models.users import Users
from src.models.searches import Searches
from src.models.postings import Postings
from src.models.companies import Companies
from src.jobs.scraping import crawl_for_postings, run_email_send_job
from src.routes import home_bp
from src.routes.auth import auth_bp
from src.routes.companies import companies_bp
from src.routes.errors import errors_bp
from src.routes.preferences import preferences_bp
from src.routes.scraping import scraping_bp
from src.routes.searches import searches_bp

## Logging
import logging
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

## Auth
from flask_login import current_user, LoginManager

## Misc
import os

## Set up the background scheduler
sched = BackgroundScheduler()

## Set up Sentry
if os.environ.get("ENV") == "PROD":
    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_DSN"),
        integrations=[
            FlaskIntegration(),
        ],

        traces_sample_rate=1.0
    )

app = Flask(__name__, static_folder = "static", template_folder = "templates")
admin = Admin(app, name='jobcrawler')

app.register_blueprint(home_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(companies_bp)
app.register_blueprint(errors_bp)
app.register_blueprint(preferences_bp)
app.register_blueprint(scraping_bp)
app.register_blueprint(searches_bp)


class AdminView(ModelView):
    def is_accessible(self):
        if current_user.get_id():
            return current_user.email == "mrkaye97@gmail.com"
        else:
            return False

admin.add_view(AdminView(Users, db.session))
admin.add_view(AdminView(Postings, db.session))
admin.add_view(AdminView(Companies, db.session))
admin.add_view(AdminView(Searches, db.session))

admin.add_link(MenuLink(name = 'Home', category = '', url = "/index"))

app.secret_key = os.urandom(24)

root = logging.getLogger()
root.setLevel(logging.INFO)

app.config.from_object(Config)
migrate = Migrate(app, db)
db.init_app(app)
migrate.init_app(app, db)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

login_manager = LoginManager()
login_manager.login_view = 'auth_bp.login'
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
