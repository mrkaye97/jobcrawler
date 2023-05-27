## Flask imports
from flask import current_app, Flask
from jobcrawler import db
from sqlalchemy import text

## Application Imports
from jobcrawler.models.companies import Companies
from jobcrawler.models.postings import Postings
from jobcrawler.exceptions.exceptions import ScrapingException

## Imports for scraping
import requests
import traceback
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

## Misc Imports
from sentry_sdk import capture_message
import sib_api_v3_sdk
import os
import datetime
import re
from sqlalchemy import text
from uuid import UUID
from typing import List, Dict, Tuple
from itertools import groupby
from operator import attrgetter

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
    r = requests.get(url)

    if r.status_code == 404:
        raise ScrapingException(
            url=url, code=400, message=f"The following URL just 404ed: {url}"
        )

    return r


def send_email(sender_name: str, sender_email: str, recipient: str, subject: str, body: str) -> requests.Response:
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = os.environ.get("SIB_API_KEY")

    # create an instance of the API class
    api_instance = sib_api_v3_sdk.AccountApi(sib_api_v3_sdk.ApiClient(configuration))
    sender = sib_api_v3_sdk.SendSmtpEmailSender(name=sender_name, email=sender_email)
    to = [sib_api_v3_sdk.SendSmtpEmailTo(email=recipient)]

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        sender=sender, to=to, subject=subject, html_content=body
    )

    response = api_instance.send_transac_email(send_smtp_email)

    return response


def get_links_selenium(driver: webdriver.Chrome, url: str, example_prefix: str) -> List[Dict[str, str]]:
    ## Check if the page loads without 404ing
    load_page(url)

    result = []

    try:
        current_app.logger.info(f"Getting {url}")
        driver.get(url)
        current_app.logger.info(f"Finished getting {url}")

        links = driver.find_elements(By.XPATH, "//a[@href]")

        for link in links:
            href = link.get_attribute("href")
            current_app.logger.info(f"Found link {href}")
            if example_prefix in href:
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

    soup = BeautifulSoup(r.content, features="html.parser")

    links = lambda tag: (getattr(tag, "name", None) == "a" and "href" in tag.attrs)

    links = soup.find_all(links)

    useful_links = filter(
        lambda x: example_prefix in urljoin(url, x["href"]) and (
                "lever" not in url
                or is_valid_uuid(urljoin(url, x["href"]).rsplit("/", 1)[-1])
        ),
        links
    )

    return list(
        map(
            lambda x: {"text": extract_link_text(x, url), "href": urljoin(url, x["href"])},
            useful_links
        )
    )

def get_links(driver: webdriver.Chrome, company: Companies) -> List:
    if company.scraping_method == "selenium":
        return get_links_selenium(
            driver=driver,
            url=company.board_url,
            example_prefix=company.job_posting_url_prefix,
        )
    elif company.scraping_method == "soup":
        return get_links_soup(
            url=company.board_url, example_prefix=company.job_posting_url_prefix
        )
    else:
        return []

def crawl_for_postings(app: Flask) -> None:
    ## Set up Selenium
    driver = create_driver()

    with app.app_context():
        for company in Companies.query.all():
            current_app.logger.info(f"Scraping {company.name}'s job board")
            links = get_links(driver=driver, company=company)
            current_app.logger.info(f"Finished scraping {company.name}'s job board")

            existing_postings = Postings.query.filter_by(company_id=company.id).all()
            existing_links = map(lambda x: x.link_href, existing_postings)

            for link in links:
                if not link.get("href") in existing_links:
                    current_app.logger.info(f"Adding new posting for {link.get('href')}")
                    new_posting = Postings(
                        company_id=company.id,
                        link_text=link.get("text"),
                        link_href=link.get("href"),
                    )
                    db.session.add(new_posting)

            new_links = [l.get("href") for l in links]
            for link in existing_links:
                if not link in new_links:
                    current_app.logger.info(f"Deleting record for {link}")
                    db.session.execute(
                        text(f"DELETE FROM postings WHERE link_href = '{link}'")
                    )

            current_app.logger.info("Committing changes.")
            db.session.commit()

    driver.quit()


def is_matching_posting(search: Tuple) -> bool:
    if not search.search_regex or not search.link_text:
        return False

    return re.search(search.search_regex.lower(), search.link_text.lower())

def is_recent_posting(search: Tuple) -> bool:
    search.created_at > (
        datetime.datetime.now()
        - datetime.timedelta(days=search.email_frequency_days)
    )

def create_posting_advertisement(search: Tuple) -> bool:
    clean_link_text = re.sub(r"(\w)([A-Z])", r"\1 - \2", search.link_text)
    return {"text": f"{clean_link_text}", "href": search.link_href}


def get_user_job_searches() -> List[Tuple]:
    current_day = (datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).days

    return db.session.execute(
        text(
            """
            SELECT
                u.id AS user_id,
                u.email_frequency_days,
                u.email,
                u.first_name,
                c.name AS company_name,
                s.search_regex,
                p.link_href,
                p.link_text,
                p.created_at
            FROM searches s
            JOIN companies c ON c.id = s.company_id
            JOIN postings p ON p.company_id = c.id
            JOIN users u ON u.id = s.user_id
            WHERE
                MOD(:current_day, email_frequency_days) = 0
                OR is_admin
            """
        ),
        {"current_day": current_day}
    ).all() or []


def generate_link_html(posting: Dict[str, str]) -> str:
    current_app.logger.info(f"Posting: {posting}")
    return f"""
        <li><a href="{posting.get('href')}">{posting.get('text')}</a></li>
    """


def generate_email_html(first_name: str, matching_postings: Dict[List[str, str]], email_frequency_days: int) -> str:
    all_postings = {}
    for company, jobs in matching_postings.items():
        all_postings[company] = "".join([generate_link_html(job) for job in jobs])

    all_htmls = "".join(
        [
            f"""
                <h4>{company}</h4>
                <ul>
                {postings}
                </ul>
            """
            for company, postings in all_postings.items()
        ]
    )

    return f"""
        <p>Hey {first_name},</p>
        <p>Here are your links for the day!</p>
        <br>
        {all_htmls}
        <br>
        <p>I&#39;ll send you another round of matching links in {email_frequency_days} day{'s' if email_frequency_days > 1 else ''}.</p>
        <p>Have a good one!</p>
        <p>Matt</p>
    """


def run_email_send_job(app: Flask) -> None:
    with app.app_context():
        searches = {email: list(data) for email, data in groupby(get_user_job_searches(), attrgetter('email'))}

        for email, searches in searches.items():
            current_app.logger.info(f"Preparing to send email to {email}")

            relevant_postings = filter(
                lambda x: is_matching_posting(x) and is_recent_posting(x),
                searches
            )

            ads = list(
                map(
                    lambda x: {"company_name": x.company_name, "ad": create_posting_advertisement(x)},
                    relevant_postings
                )
            )

            companies = set(
                map(
                    lambda x: x.get("company_name"),
                    ads
                )
            )

            links_by_company = {company: [ad.get("ad") for ad in ads if ad.get("company_name") == company] for company in companies}

            if links_by_company:
                message = generate_email_html(
                    first_name=searches[0].first_name,
                    matching_postings=links_by_company,
                    email_frequency_days=searches[0].email_frequency_days,
                )

                if os.environ.get("ENV") == "PROD" and os.environ.get("SIB_API_KEY"):
                    current_app.logger.info(f"Sending email to {email}")
                    send_email(
                        sender_email="mrkaye97@gmail.com",
                        sender_name="Matt Kaye",
                        recipient=email,
                        subject="Your job feed digest",
                        body=message,
                    )
