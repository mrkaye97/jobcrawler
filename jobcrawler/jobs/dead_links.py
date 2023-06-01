## Flask imports
from flask import current_app
from jobcrawler import db

## Application Imports
from jobcrawler.models.companies import Companies
from jobcrawler.jobs.scraping import load_page

def test_links() -> None:
    for company in Companies.query.all():
        current_app.logger.info(f"Testing board URL for {company.name}")
        result = load_page(company.board_url)

        if not result or result.status_code != 200:
            current_app.logger.info(f"Found a dead link at {company.board_url}")
            company.board_url_is_dead_link = True
            db.session.commit()
