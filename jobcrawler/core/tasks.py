from jobcrawler.email.email import run_email_send_job
from jobcrawler.scraping.dead_links import test_for_dead_links
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
        hour=random.randint(0, 22),
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
    )

sched.add_job(id="send_emails", func=run_email_send_job, trigger="cron", hour=0)

sched.add_job(id="check_dead_links", func=test_for_dead_links, trigger="cron", hour=10)
