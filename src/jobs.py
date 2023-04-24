from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
import sib_api_v3_sdk
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from .models import Users, Companies, Postings, Searches
import datetime
import re
from sqlalchemy import text

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

def get_links_selenium(url, example_prefix):
    DRIVER="geckodriver"
    service = Service(executable_path=DRIVER)
    driver = webdriver.Firefox(service=service)
    delay = 3

    driver.implicitly_wait(delay)
    driver.get(url)

    links =  driver.find_elements(By.XPATH, "//a[@href]")

    result =  [
        {
            "text": link.get_attribute("text"),
            "href": link.get_attribute("href")
        }
        for link in links
        if example_prefix in link.get_attribute("href")
    ]

    driver.quit()

    return result


def get_links_lever():
    pass

def get_links_greenhouse():
    pass

def get_links_soup(url, example_prefix):
    r = requests.get(url)
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
    with app.app_context():
        for company in Companies.query.all():
            app.logger.info(f"Scraping {company.name}'s job board")
            if company.scraping_method == 'selenium':
                links = get_links_selenium(url = company.board_url, example_prefix = company.job_posting_url_prefix)
            elif company.scraping_method == 'soup':
                links = get_links_soup(url = company.board_url, example_prefix = company.job_posting_url_prefix)
            else:
                links = []

            app.logger.info(f"Finished scraping {company.name}'s job board")
            app.logger.info(f"Removing existing links for {company.name}")

            existing_postings = Postings.query.filter_by(company_id = company.id).all()

            if existing_postings:
                db.session.execute(text(f'delete from postings where company_id = {company.id}'))

            app.logger.info(f"Finished removing existing links for {company.name}")
            app.logger.info(f"Adding new links for {company.name}")

            for link in links:
                new_posting = Postings(company_id = company.id, link_text = link["text"], link_href = link["href"])
                db.session.add(new_posting)

            app.logger.info("Committing changes.")
            db.session.commit()

def run_email_send_job(app):
    with app.app_context():
        current_day = (datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).days

        ## TODO: Instead of first pulling all users and then check
        ## if the email frequency matches, just do this filter in the db in the second query
        for user in Users.query.all():
            ## TODO: Replace `user_email_frequencies` with the frequency of
            ## the individual user
            Searches.\
                query.\
                join(Companies).\
                with_entities(Searches.id.label("search_id"), Companies.id.label("company_id"), Companies.name, Companies.board_url, Searches.search_regex, Companies.scraping_method).\
                all()

            user_email_frequency = user.email_frequency_days or 7

            ## Replace with current_date % user_email_frequency
            if True:
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

                matching_postings = [
                    f"{search.link_text} @ {search.company_name}: {search.link_href}"
                    for search in user_search_results
                    if re.search(search.search_regex, search.link_text)
                ]

                link_text = "\n".join(matching_postings)

                message = f"""
                    Hey {user_search_results.name},

                    Here are your links for the day!

                    {link_text}

                    Have a good one! I'll send you another round of matching links in {user_email_frequency} days.

                    Matt
                """

                if os.environ.get("ENV") == "PROD":
                    send_email(
                        sender_email = "mrkaye97@gmail.com",
                        sender_name = "Matt Kaye",
                        recipient = user_search_results.email,
                        subject = "Your daily job feed digest",
                        body = message
                    )
                else:
                    app.logger.info(message)
