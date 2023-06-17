## Flask
from flask import Flask
from config import Config

## Application
from jobcrawler.models import db
from jobcrawler.jobs.email import run_email_send_job
from jobcrawler.jobs.dead_links import test_for_dead_links
from jobcrawler.routes import home_bp
from jobcrawler.routes.auth import auth_bp
from jobcrawler.routes.companies import companies_bp
from jobcrawler.routes.errors import errors_bp
from jobcrawler.routes.preferences import preferences_bp
from jobcrawler.routes.scraping import scraping_bp
from jobcrawler.routes.searches import searches_bp
from jobcrawler.extensions.scheduler import sched
from jobcrawler.jobs.scraping import create_scraping_jobs

## Logging
import logging
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

## Misc
import os

## Extensions
from jobcrawler.extensions.admin import admin
from jobcrawler.extensions.migrate import migrate
from jobcrawler.extensions.login_manager import login_manager
from jobcrawler.extensions.sitemap import sitemap

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
    app.config.from_object(config_class)

    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(companies_bp)
    app.register_blueprint(errors_bp)
    app.register_blueprint(preferences_bp)
    app.register_blueprint(scraping_bp)
    app.register_blueprint(searches_bp)

    app.secret_key = os.environ.get("APP_SECRET_KEY") or os.urandom(24)

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    admin.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    sitemap.init_app(app)

    sched.init_app(app)
    sched.start()

    @app.teardown_request
    def teardown_request(exception):
        if exception:
            db.session.rollback()
        db.session.remove()


    if __name__ != "__main__":
        gunicorn_logger = logging.getLogger("gunicorn.error")
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)


    ## Don't run the scheduler in pytest session
    if not os.environ.get("PYTEST_CURRENT_TEST"):

        app.logger.info("Creating scraping jobs")
        with sched.app.app_context():
            create_scraping_jobs(app=app)

        @sched.task(trigger="cron", hour=0, id="send_emails")
        def send_emails():
            app.logger.info("Kicking off email sending job")
            with sched.app.app_context():
                run_email_send_job(app)

        @sched.task(trigger="cron", hour=10, id="check_dead_links")
        def check_dead_links():
            app.logger.info("Kicking off dead link checking job")
            test_for_dead_links(app)



    return app
