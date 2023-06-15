from .scheduler import sched
from .scraping import crawl_for_postings
from .email import run_email_send_job
from .dead_links import test_for_dead_links

from flask import current_app

#@sched.scheduled_job(trigger="cron", hour=23, id="crawl")
@sched.scheduled_job(trigger="interval", seconds=3, id="crawl")
def crawl():
    current_app.logger.info("Kicking off scraping job")
    crawl_for_postings(current_app)

@sched.scheduled_job(trigger="cron", hour=0, id="send_emails")
def send_emails():
    current_app.logger.info("Kicking off email sending job")
    run_email_send_job(current_app)

@sched.scheduled_job(trigger="cron", hour=10, id="check_dead_links")
def check_dead_links():
    current_app.logger.info("Kicking off dead link checking job")
    test_for_dead_links(current_app)
