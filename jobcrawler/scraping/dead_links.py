## Flask imports
from flask import current_app
from jobcrawler import db

## Application Imports
from jobcrawler.core.models import Companies
from jobcrawler.scraping.postings import load_page
from jobcrawler.extensions.scheduler import sched
from jobcrawler.email.email import send_email
from sqlalchemy import text

## Sentry
from sentry_sdk import capture_message

from typing import List, Tuple


def test_for_dead_links() -> List[Tuple[str, str]]:
    dead_links = []
    with sched.app.app_context():
        current_app.logger.info("Kicking off dead link checking job")
        for company in Companies.query.all():
            url = company.board_url
            current_app.logger.info(f"Testing board URL for {company.name}")
            result = load_page(url)

            if result is None or result.status_code != 200:
                current_app.logger.info(f"Found a dead link at {url}")
                company.board_url_is_dead_link = True
                db.session.commit()

                dead_links = dead_links + [(company.name, url)]
            elif company.board_url_is_dead_link:
                current_app.logger.info(
                    f"Found working link for {url}. Resetting `is_dead_link` to False."
                )

                company.board_url_is_dead_link = False
                db.session.commit()

        capture_message(f"Found dead links for the following: {dead_links}")

    return dead_links


def send_dead_links_notification_email() -> None:
    with sched.app.app_context():
        current_app.logger.info("Running dead link notification job")
        dead_links = db.session.execute(
            text("SELECT name, board_url FROM companies WHERE board_url_is_dead_link;")
        ).all()

        if dead_links:
            dead_link_html_list = "\n".join(
                [f'<li><a href="{l.board_url}">{l.name}</a></li>' for l in dead_links]
            )
            current_app.logger.info(dead_link_html_list)

            send_email(
                "Matt",
                "mrkaye97@gmail.com",
                "mrkaye97@gmail.com",
                "Dead Links Report",
                f"""
                Hey Matt,

                I found some dead links this week. You might want to check them out to get them back online.

                <ul>
                {dead_link_html_list}
                </ul>

                Thanks!
                """,
            )
