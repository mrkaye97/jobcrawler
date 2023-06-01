## Flask imports
from flask import current_app
from jobcrawler import db

## Application Imports
from jobcrawler.models.companies import Companies
from jobcrawler.jobs.scraping import load_page

## Sentry
from sentry_sdk import capture_message

from typing import List, Tuple

def test_for_dead_links() -> List[Tuple[str, str]]:
    dead_links = []
    for company in Companies.query.all():
        current_app.logger.info(f"Testing board URL for {company.name}")
        result = load_page(company.board_url)

        if result is None or result.status_code != 200:
            current_app.logger.info(f"Found a dead link at {company.board_url}")
            company.board_url_is_dead_link = True
            db.session.commit()

            dead_links = dead_links + [(company.name, company.board_url)]

    capture_message(f"Found dead links for the following: {dead_links}")
    return dead_links
