## Flask imports
from flask import current_app

## current_application Imports
from jobcrawler.models.companies import Companies
from jobcrawler.models.postings import Postings
from jobcrawler.models.users import Users
from jobcrawler.models.searches import Searches
from jobcrawler.exceptions import ScrapingException

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

def load_page(url):
    r = requests.get(url)

    if r.status_code == 404:
        raise ScrapingException(url = url, code = 400, message = f"The following URL just 404ed: {url}")

    return r

def send_email(sender_name, sender_email, recipient, subject, body):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = os.environ.get("SIB_API_KEY")

    # create an instance of the API class
    api_instance = sib_api_v3_sdk.AccountApi(sib_api_v3_sdk.ApiClient(configuration))
    sender = sib_api_v3_sdk.SendSmtpEmailSender(name = sender_name, email = sender_email)
    to = [sib_api_v3_sdk.SendSmtpEmailTo(email = recipient)]

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(sender = sender, to = to, subject = subject, text_content = body)

    response = api_instance.send_transac_email(send_smtp_email)

    return response

def get_links_selenium(driver, url, example_prefix):
    ## Check if the page loads without 404ing
    load_page(url)

    result = []

    try:
        current_app.logger.info(f"Getting {url}")
        driver.get(url)
        current_app.logger.info(f"Finished getting {url}")

        links =  driver.find_elements(By.XPATH, "//a[@href]")

        for link in links:
            href = link.get_attribute("href")
            current_app.logger.info(f"Found link {href}")
            if example_prefix in href:
                result = result + [{
                    "text": link.get_attribute("text"),
                    "href": href
                }]

    except Exception as e:
        message = f"""
            Failed to get links for {url}.

            Error: {traceback.format_exc()}
        """

        current_app.logger.error(message)
        capture_message(message)

    return result

def get_links_soup(url, example_prefix):
    r = load_page(url)

    soup = BeautifulSoup(r.content, features="html.parser")

    links = lambda tag: (getattr(tag, 'name', None) == 'a' and 'href' in tag.attrs)

    links = soup.find_all(links)

    return [
        {
            "text": link.contents[0].text if 'lever' in url else link.string,
            "href": urljoin(url, link['href'])
        }
        for link in links
        if example_prefix in urljoin(url, link['href'])
    ]

def crawl_for_postings(app, db):

    ## Set up Selenium
    driver = webdriver.Chrome(options=set_chrome_options())
    delay = 3

    driver.implicitly_wait(delay)

    with app.app_context():
        for company in Companies.query.all():
            current_app.logger.info(f"Scraping {company.name}'s job board")
            if company.scraping_method == 'selenium':
                links = get_links_selenium(driver = driver, url = company.board_url, example_prefix = company.job_posting_url_prefix)
            elif company.scraping_method == 'soup':
                links = get_links_soup(url = company.board_url, example_prefix = company.job_posting_url_prefix)
            else:
                links = []

            current_app.logger.info(f"Finished scraping {company.name}'s job board")
            current_app.logger.info(f"Removing existing links for {company.name}")

            existing_postings = Postings.query.filter_by(company_id = company.id).all()

            if existing_postings:
                db.session.execute(text(f'delete from postings where company_id = {company.id}'))

            current_app.logger.info(f"Finished removing existing links for {company.name}")
            current_app.logger.info(f"Adding new links for {company.name}")

            for link in links:
                new_posting = Postings(company_id = company.id, link_text = link["text"], link_href = link["href"])
                db.session.add(new_posting)

            current_app.logger.info("Committing changes.")
            db.session.commit()

    driver.quit()

    return None

def run_email_send_job(app, is_manual_trigger = False):
    with app.app_context():
        current_day = (datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).days

        ## TODO: Instead of first pulling all users and then check
        ## if the email frequency matches, just do this filter in the db in the second query
        for user in Users.query.all():
            if not is_manual_trigger or (is_manual_trigger and user.email == "mrkaye97@gmail.com"):
                user_email_frequency = user.email_frequency_days or 7

                if current_day % user_email_frequency == 0 or user.email == "mrkaye97@gmail.com":
                    current_app.logger.info(f"Preparing to send email to {user.email}")
                    user_search_results = Searches.\
                        query.\
                        filter_by(user_id = user.id).\
                        join(Companies).\
                        join(Postings).\
                        join(Users).\
                        with_entities(
                            Users.email,
                            Users.first_name,
                            Companies.name.label("company_name"),
                            Searches.search_regex,
                            Postings.link_href,
                            Postings.link_text,
                        ).\
                        all()

                    if user_search_results:

                        matching_postings = []

                        for search in user_search_results:
                            if re.search(search.search_regex.lower(), search.link_text.lower() if search.link_text and search.search_regex else ""):
                                clean_link_text = re.sub(r"(\w)([A-Z])", r"\1 - \2", search.link_text)
                                matching_postings = matching_postings + [f"{clean_link_text} @ {search.company_name}: {search.link_href}"]

                        current_app.logger.info(f"Matching job postings: {matching_postings}")

                        if matching_postings:

                            link_text = "\n".join(matching_postings)

                            message = f"""
                                Hey {user.first_name},

                                Here are your links for the day!

                                {link_text}

                                I'll send you another round of matching links in {user_email_frequency} days.

                                Have a good one!

                                Matt
                            """

                            current_app.logger.info(f"Email message: {message}")

                            if os.environ.get("ENV") == "PROD":
                                current_app.logger.info(f"Sending email to {user.email}")
                                send_email(
                                    sender_email = "mrkaye97@gmail.com",
                                    sender_name = "Matt Kaye",
                                    recipient = user.email,
                                    subject = "Your daily job feed digest",
                                    body = message
                                )
                            else:
                                current_app.logger.info(message)
