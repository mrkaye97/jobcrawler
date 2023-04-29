## Application Imports
from src import db
from src.jobs.scraping import set_chrome_options, get_links_selenium, get_links_soup, crawl_for_postings, run_email_send_job
from src.models.companies import Companies
from src.exceptions import CompanyExistsException, ScrapingException
## Flask Imports
from flask import request, Blueprint, current_app

## Selenium Imports
from selenium import webdriver

scraping_bp = Blueprint('scraping_bp', __name__, template_folder='templates', static_folder = "static")

@scraping_bp.route('/scraping/test', methods = ["POST"])
def test_scraping():

    ## Set up Selenium
    driver = webdriver.Chrome(options=set_chrome_options())
    delay = 3

    driver.implicitly_wait(delay)

    content = request.json

    posting_url_prefix = content.get("job_posting_url_prefix")
    board_url = content.get("board_url")
    scraping_method = content.get("scraping_method")
    company_name = content.get("name")

    existing = Companies.query.filter_by(name = company_name).count()

    if existing:
        raise CompanyExistsException(name = company_name)

    if scraping_method == "soup":
        links = get_links_soup(
            url = board_url,
            example_prefix = posting_url_prefix
        )
    elif scraping_method == "selenium":
        links = get_links_selenium(
            driver = driver,
            url = board_url,
            example_prefix = posting_url_prefix
        )
    else:
        return "Could not find that scraping method", 400

    matching_links = [l for l in links if posting_url_prefix in l.get("href")]
    if not matching_links:
        raise ScrapingException(message = f"No links found matching {posting_url_prefix} at {board_url} with scraping method {scraping_method}", code = 400)

    driver.quit()
    return matching_links

@scraping_bp.route('/scraping/run-crawl-job', methods = ["POST"])
def manually_trigger_crawl_job():
    current_app.logger.info("Kicking off scraping job")
    crawl_for_postings(db)
    current_app.logger.info("Finished scraping job")

    return {"message": "finished"}, 200

@scraping_bp.route('/scraping/run-email-job', methods = ["POST"])
def manually_trigger_email_sending_job():
    current_app.logger.info("Kicking off email job")
    print("Kicking off email job")
    run_email_send_job(is_manual_trigger = True)
    current_app.logger.info("Finished email job")

    return {"message": "finished"}, 200
