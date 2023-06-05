## Flask imports
from flask import current_app, Flask
from jobcrawler import db

## Application Imports
from jobcrawler.models.companies import Companies
from jobcrawler.jobs.scraping import load_page

## Sentry
from sentry_sdk import capture_message

from typing import List, Tuple

def test_for_dead_links(app: Flask) -> List[Tuple[str, str]]:
    with app.app_context():
        dead_links = []

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
                current_app.logger.info(f"Found working link for {url}. Resetting `is_dead_link` to False.")

                company.board_url_is_dead_link = False
                db.session.commit()

        capture_message(f"Found dead links for the following: {dead_links}")
        return dead_links
