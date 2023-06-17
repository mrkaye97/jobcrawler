from jobcrawler.jobs.email import run_email_send_job
from jobcrawler.jobs.dead_links import test_for_dead_links
from jobcrawler.jobs.scraping import create_scraping_jobs

from jobcrawler.extensions.scheduler import sched

from flask import current_app

create_scraping_jobs()

@sched.task(trigger="cron", hour=0, id="send_emails")
def send_emails():
    run_email_send_job()

@sched.task(trigger="cron", hour=10, id="check_dead_links")
def check_dead_links():
    test_for_dead_links()
