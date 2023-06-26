from jobcrawler.email.email import run_email_send_job
from jobcrawler.scraping.dead_links import (
    test_for_dead_links,
    send_dead_links_notification_email,
)
from jobcrawler.scraping.postings import crawl_for_postings

from jobcrawler.core.models import Companies
from jobcrawler.extensions.scheduler import sched

import random

with sched.app.app_context():
    companies = Companies.query.all()

for company in companies:
    sched.add_job(
        id=f"scrape-{company.id}",
        func=crawl_for_postings,
        kwargs={"company": company},
        trigger="cron",
        hour=22,
        jitter = 3600
    )

sched.add_job(id="send_emails", func=run_email_send_job, trigger="cron", hour=0)

sched.add_job(id="check_dead_links", func=test_for_dead_links, trigger="cron", hour=10)

sched.add_job(
    id="dead_link_email",
    func=send_dead_links_notification_email,
    trigger="cron",
    day=4,
    hour=20,
)
