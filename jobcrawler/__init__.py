## Flask
from flask import Flask
from flask_admin import Admin
from flask_admin.menu import MenuLink
from flask_admin.contrib.sqla import ModelView
from config import Config
from flask_migrate import Migrate
from flask_sitemap import Sitemap

## Application
from jobcrawler.models import db
from jobcrawler.models.users import Users
from jobcrawler.models.searches import Searches
from jobcrawler.models.postings import Postings
from jobcrawler.models.companies import Companies
from jobcrawler.jobs.scraping import crawl_for_postings
from jobcrawler.jobs.email import run_email_send_job
from jobcrawler.jobs.dead_links import test_for_dead_links
from jobcrawler.routes import home_bp
from jobcrawler.routes.auth import auth_bp
from jobcrawler.routes.companies import companies_bp
from jobcrawler.routes.errors import errors_bp
from jobcrawler.routes.preferences import preferences_bp
from jobcrawler.routes.scraping import scraping_bp
from jobcrawler.routes.searches import searches_bp
from jobcrawler.jobs.scheduler import sched
from jobcrawler.jobs.scraping import create_scraping_jobs

## Logging
import logging
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

## Auth
from flask_login import current_user, LoginManager

## Misc
import os


def create_app(config_class=Config):
    ## Set up Sentry
    if os.environ.get("ENV") == "PROD":
        sentry_sdk.init(
            dsn=os.environ.get("SENTRY_DSN"),
            integrations=[
                FlaskIntegration(),
            ],
            traces_sample_rate=1.0,
        )

    app = Flask(__name__, static_folder="static", template_folder="templates")

    ext = Sitemap(app=app)

    admin = Admin(app, name="jobcrawler")

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
                return current_user.is_admin
            else:
                return False

    admin.add_view(AdminView(Users, db.session))
    admin.add_view(AdminView(Postings, db.session))
    admin.add_view(AdminView(Companies, db.session))
    admin.add_view(AdminView(Searches, db.session))

    admin.add_link(MenuLink(name="Home", category="", url="/index"))

    app.secret_key = os.environ.get("APP_SECRET_KEY") or os.urandom(24)

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    app.config.from_object(config_class)
    migrate = Migrate(app, db)
    db.init_app(app)
    migrate.init_app(app, db)

    if __name__ != "__main__":
        gunicorn_logger = logging.getLogger("gunicorn.error")
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

    login_manager = LoginManager()
    login_manager.login_view = "auth_bp.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Users, user_id)

    ## Don't run the scheduler in pytest session
    if not os.environ.get("PYTEST_CURRENT_TEST"):
        app.logger.info("Creating scraping jobs")
        create_scraping_jobs(app=app)

        @sched.scheduled_job(trigger="cron", hour=0, id="send_emails")
        def send_emails():
            app.logger.info("Kicking off email sending job")
            run_email_send_job(app)

        @sched.scheduled_job(trigger="cron", hour=10, id="check_dead_links")
        def check_dead_links():
            app.logger.info("Kicking off dead link checking job")
            test_for_dead_links(app)

        sched.start()

    return app
