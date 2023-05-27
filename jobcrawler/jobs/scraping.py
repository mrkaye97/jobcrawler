## Flask imports
from flask import current_app, Flask
from jobcrawler import db
from sqlalchemy import text, db
from typing import List, Dict

## current_application Imports
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


def is_valid_uuid(uuid_to_test: str, version: int = 4) -> bool:
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


def send_email(
    sender_name: str, sender_email: str, recipient: str, subject: str, body: str
) -> None:
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


def get_links_selenium(
    driver: webdriver.Chrome, url: str, example_prefix: str
) -> List[Dict[str, str]]:
    load_page(url)
    result = []

    try:
        current_app.logger.info(f"Getting {url}")
        driver.get(url)
        current_app.logger.info(f"Finished getting {url}")

        links = driver.find_elements(By.XPATH, "//a[@href]")
        result = list(
            map(
                lambda link: {
                    "text": link.get_attribute("text"),
                    "href": link.get_attribute("href"),
                },
                filter(
                    lambda link: example_prefix in link.get_attribute("href"), links
                ),
            )
        )

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
    full_links = map(lambda link: urljoin(url, link["href"]), links)

    valid_links = filter(
        lambda link: example_prefix in link
        and ("lever" not in url or is_valid_uuid(link.rsplit("/", 1)[-1])),
        full_links,
    )

    return [
        {"text": extract_link_text(link, url), "href": link} for link in valid_links
    ]


def crawl_for_postings(app: Flask, db) -> None:
    driver = create_driver()

    with app.app_context():
        companies = Companies.query.all()

        def handle_company(company: Companies) -> None:
            current_app.logger.info(f"Scraping {company.name}'s job board")
            links = (
                get_links_selenium(
                    driver=driver,
                    url=company.board_url,
                    example_prefix=company.job_posting_url_prefix,
                )
                if company.scraping_method == "selenium"
                else (
                    get_links_soup(
                        url=company.board_url,
                        example_prefix=company.job_posting_url_prefix,
                    )
                    if company.scraping_method == "soup"
                    else []
                )
            )

            current_app.logger.info(f"Finished scraping {company.name}'s job board")
            existing_postings = Postings.query.filter_by(company_id=company.id).all()
            existing_links = {p.link_href for p in existing_postings}

            new_links = [
                link["href"] for link in links if link["href"] not in existing_links
            ]
            deleted_links = [link for link in existing_links if link not in new_links]

            for link in new_links:
                current_app.logger.info(link)
                new_posting = Postings(
                    company_id=company.id,
                    link_text=link.get("text"),
                    link_href=link.get("href"),
                )
                db.session.add(new_posting)

            for link in deleted_links:
                current_app.logger.info(f"Deleting record for {link}")
                db.session.execute(
                    text(f"DELETE FROM postings WHERE link_href = '{link}'")
                )

            current_app.logger.info("Committing changes.")
            db.session.commit()

        list(map(handle_company, companies))

    driver.quit()

    return None


def is_matching_posting(regex: str, text: str) -> bool:
    if not regex or not text:
        return False

    return re.search(regex.lower(), text.lower())


def create_posting_advertisement(text: str, href: str) -> Dict[str, str]:
    clean_link_text = re.sub(r"(\w)([A-Z])", r"\1 - \2", text)
    return {"text": f"{clean_link_text}", "href": href}


def get_users_to_email() -> List:
    current_day = (datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).days

    users_to_email = db.session.execute(
        text(
            """
            SELECT id, email, email_frequency_days, first_name
            FROM users
            WHERE
                MOD(:current_day, email_frequency_days) = 0
                OR is_admin
            """
        ),
        {"current_day": current_day},
    ).all()

    return users_to_email or []


def get_user_job_searches(user_id: int) -> List:
    result = db.session.execute(
        text(
            """
            SELECT
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
            WHERE s.user_id = :user_id
            """
        ),
        {"user_id": user_id},
    ).all()

    return result or []


def generate_link_html(posting: Dict[str, str]) -> str:
    current_app.logger.info(f"Posting: {posting}")
    return f"""
        <li><a href="{posting.get('href')}">{posting.get('text')}</a></li>
    """


def generate_postings_html(postings: List[Dict[str, str]]) -> str:
    return "".join([generate_link_html(posting) for posting in postings])


def generate_email_html(
    first_name: str,
    matching_postings: Dict[str, List[Dict[str, str]]],
    email_frequency_days: int,
) -> str:
    postings_html = "\n".join(
        [
            f"""
            <h4>{company}</h4>
            <ul>
            {generate_postings_html(postings)}
            </ul>
        """
            for company, postings in matching_postings.items()
        ]
    )

    return f"""
        <p>Hey {first_name},</p>
        <p>Here are your links for the day!</p>
        <br>
        {postings_html}
        <br>
        <p>I'll send you another round of matching links in {email_frequency_days} day(s).</p>
        <p>If you have any feedback, reply to this email and let me know!</p>
    """


def run_email_send_job(app):
    with app.app_context():
        for user in get_users_to_email():
            user_searches = get_user_job_searches(user.id)

            current_app.logger.info(f"Preparing to send email to {user.email}")
            current_app.logger.info(f"User searches for {user.email}: {user_searches}")

            matching_postings = {}
            for search in user_searches:
                current_app.logger.info(search)
                if is_matching_posting(
                    search.search_regex, search.link_text
                ) and search.created_at > (
                    datetime.datetime.now()
                    - datetime.timedelta(days=user.email_frequency_days)
                ):
                    ad = create_posting_advertisement(
                        search.link_text, search.company_name, search.link_href
                    )

                    existing = matching_postings.get(search.company_name)
                    matching_postings[search.company_name] = (
                        [ad] if not existing else existing + [ad]
                    )

            if matching_postings:
                message = generate_email_html(
                    first_name=user.first_name,
                    matching_postings=matching_postings,
                    email_frequency_days=user.email_frequency_days,
                )

                current_app.logger.info(f"Email message: {message}")

                if os.environ.get("ENV") == "PROD" and os.environ.get("SIB_API_KEY"):
                    current_app.logger.info(f"Sending email to {user.email}")
                    send_email(
                        sender_email="mrkaye97@gmail.com",
                        sender_name="Matt Kaye",
                        recipient=user.email,
                        subject="Your job feed digest",
                        body=message,
                    )
