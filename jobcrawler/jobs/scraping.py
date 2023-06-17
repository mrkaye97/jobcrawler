## Flask imports
from flask import current_app, Flask
from jobcrawler.models import db
from sqlalchemy import text

## Application Imports
from jobcrawler.models.companies import Companies
from jobcrawler.models.postings import Postings
from jobcrawler.exceptions.exceptions import ScrapingException
from jobcrawler.extensions.scheduler import sched

## Imports for scraping
import requests
import traceback
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

## Misc Imports
from sentry_sdk import capture_message, capture_exception
import os
import re
from sqlalchemy import text
from uuid import UUID
from typing import List, Dict
import time
import random

from jobcrawler.extensions.scheduler import sched


def is_valid_uuid(uuid_to_test, version=4):
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test


def set_chrome_options() -> Options:
    """Sets chrome options for Selenium.
    Chrome options for headless browser is enabled.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    return chrome_options


def create_driver() -> webdriver.Chrome:
    driver = webdriver.Chrome(options=set_chrome_options())
    delay = 3

    driver.implicitly_wait(delay)

    return driver


def load_page(url: str) -> requests.Response:
    try:
        r = requests.get(url)
    except:
        capture_exception(
            ScrapingException(
                url=url, code=400, message=f"There was an error loading {url}"
            )
        )

        return None

    if r.status_code == 404:
        capture_exception(
            ScrapingException(
                url=url, code=400, message=f"The following URL just 404ed: {url}"
            )
        )

    return r


def strip_scheme(url):
    return re.sub(r"^http(s)?:\/\/", "", url)


def link_is_job_posting(prefix: str, url: str) -> bool:
    prefix = strip_scheme(prefix)
    url = strip_scheme(url)

    return prefix in url


def get_links_selenium(
    driver: webdriver.Chrome, url: str, example_prefix: str
) -> List[Dict[str, str]]:
    ## Check if the page loads without 404ing
    load_page(url)

    result = []

    try:
        current_app.logger.info(f"Getting {url}")
        driver.get(url)
        current_app.logger.info(f"Finished getting {url}")

        time.sleep(3)

        links = driver.find_elements(By.XPATH, "//a[@href]")

        for link in links:
            href = link.get_attribute("href")
            if link_is_job_posting(example_prefix, href):
                result = result + [{"text": link.get_attribute("text"), "href": href}]

    except Exception as e:
        message = f"""
            Failed to get links for {url}.

            Error: {traceback.format_exc()}
        """

        current_app.logger.error(message)
        if os.environ.get("ENV") == "PROD" and os.environ.get("SENTRY_DSN"):
            capture_message(message)

    return result


def extract_link_text(link: str, url: str) -> str:
    link_text = link.text
    link_string = link.string

    if "lever" in url:
        return link.contents[0].text
    elif link_text:
        return link_text.strip()
    else:
        return link_string.strip()


def get_links_soup(url: str, example_prefix: str) -> List[Dict[str, str]]:
    r = load_page(url)

    if not r:
        return []

    soup = BeautifulSoup(r.content, features="html.parser")

    links = lambda tag: (getattr(tag, "name", None) == "a" and "href" in tag.attrs)

    links = soup.find_all(links)

    useful_links = filter(
        lambda x: link_is_job_posting(example_prefix, urljoin(url, x["href"]))
        and (
            "lever" not in url
            or is_valid_uuid(urljoin(url, x["href"]).rsplit("/", 1)[-1])
        ),
        links,
    )

    return list(
        map(
            lambda x: {
                "text": extract_link_text(x, url),
                "href": urljoin(url, x["href"]),
            },
            useful_links,
        )
    )


def deduplicate_links(links: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [dict(x) for x in set(tuple(link.items()) for link in links)]


def get_links(driver: webdriver.Chrome, company: Companies) -> List:
    if company.scraping_method == "selenium":
        links = get_links_selenium(
            driver=driver,
            url=company.board_url,
            example_prefix=company.job_posting_url_prefix,
        )
    elif company.scraping_method == "soup":
        links = get_links_soup(
            url=company.board_url, example_prefix=company.job_posting_url_prefix
        )
    else:
        links = []

    return deduplicate_links(links)


def crawl_for_postings(company: Companies) -> None:
    driver = create_driver()

    with sched.app.app_context():
        current_app.logger.info(f"Scraping {company.name}'s job board")
        links = get_links(driver=driver, company=company)
        current_app.logger.info(f"Finished scraping {company.name}'s job board")

        ## Get the postings for the company that already exist in the db
        existing_postings = Postings.query.filter_by(company_id=company.id).all()

        ## Get the links for the company that already exist in the db
        existing_links = set(map(lambda x: x.link_href, existing_postings))

        ## Get the new links we're going to add (from the scraping we just did)
        new_links = set(map(lambda x: x.get("href"), links))

        for link in existing_links:
            ## If there's a link in the database that isn't in
            ## the set we just scraped, that means that job
            ## has been taken down. In that case, we should delete
            ## the no-longer-open job from the db
            if not link in new_links:
                current_app.logger.info(f"Deleting records for {link}")
                db.session.execute(
                    text(f"DELETE FROM postings WHERE link_href = '{link}'")
                )

        for link in links:
            ## If the new link doesn't yet exist in the db
            ## we add it
            if not link.get("href") in existing_links:
                current_app.logger.info(f"Adding new posting for {link.get('href')}")
                new_posting = Postings(
                    company_id=company.id,
                    link_text=link.get("text"),
                    link_href=link.get("href"),
                )
                db.session.add(new_posting)

        current_app.logger.info("Committing changes.")
        db.session.commit()

    driver.quit()


def create_scraping_jobs(app: Flask) -> List[Dict[str, str]]:
    with sched.app.app_context():
        companies = Companies.query.all()

        for company in companies:
            sched.add_job(
                id = f"scrape-{company.id}",
                func=crawl_for_postings,
                kwargs={"company": company},
                trigger="cron",
    #            hour=random.randint(0, 22),
    #            minute=random.randint(0, 59),
                second=random.randint(0, 59),
            )
