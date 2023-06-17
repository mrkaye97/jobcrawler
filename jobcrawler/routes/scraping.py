## Application Imports
from jobcrawler import db
from jobcrawler.scraping.scraping import (
    create_driver,
    get_links,
)
from jobcrawler.models.companies import Companies
from jobcrawler.exceptions.exceptions import CompanyExistsException, ScrapingException

## Flask Imports
from flask import request, Blueprint

## Sentry
from sentry_sdk import capture_exception

scraping_bp = Blueprint(
    "scraping_bp", __name__, template_folder="templates", static_folder="static"
)


@scraping_bp.route("/scraping/test", methods=["POST"])
def test_scraping():
    ## Set up Selenium
    driver = create_driver()

    content = request.json

    posting_url_prefix = content.get("job_posting_url_prefix")
    board_url = content.get("board_url")
    scraping_method = content.get("scraping_method")
    company_name = content.get("name")

    existing = Companies.query.filter_by(name=company_name).count()

    if existing:
        raise CompanyExistsException(name=company_name)

    matching_links = get_links(
        driver,
        Companies(
            job_posting_url_prefix=posting_url_prefix,
            board_url=board_url,
            scraping_method=scraping_method,
            name=company_name,
        ),
    )

    if not matching_links:
        capture_exception(
            ScrapingException(
                url=board_url,
                message=f"No links found matching {posting_url_prefix} at {board_url} with scraping method {scraping_method}",
                code=400,
            )
        )

    driver.quit()
    return matching_links
