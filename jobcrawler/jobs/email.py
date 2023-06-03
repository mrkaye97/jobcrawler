## Flask imports
from flask import current_app, Flask
from jobcrawler import db
from sqlalchemy import text

## Application Imports
from jobcrawler.models.users import Users


## Misc Imports
import requests
import sib_api_v3_sdk
import os
import datetime
import re
from sqlalchemy import text
from typing import List, Dict, Tuple
from itertools import groupby
from operator import attrgetter


def send_email(
    sender_name: str, sender_email: str, recipient: str, subject: str, body: str
) -> requests.Response:
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


def is_matching_posting(search: Tuple) -> bool:
    if not search.search_regex or not search.link_text:
        return False

    return re.search(search.search_regex.lower(), search.link_text.lower())


def create_posting_advertisement(search: Tuple) -> bool:
    ## Naive algorithm for adding a space between two
    ## words that are probably supposed to be separate
    prev = ""
    link_text = ""
    for char in search.link_text:
        if prev.islower() and char.isupper():
            link_text = link_text + " - "

        link_text = link_text + char
        prev = char

    return {"text": f"{link_text}", "href": search.link_href}


def get_user_job_searches() -> List[Tuple]:
    return (
        db.session.execute(
            text(
                """
                SELECT
                    u.id AS user_id,
                    u.email_frequency_days,
                    u.email,
                    u.first_name,
                    u.last_received_email_at,
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
                    (
                        -- If you've never gotten an email or
                        -- If the posting was created more recently
                        -- than your last one, we'll include it
                        p.created_at > COALESCE(u.last_received_email_at, '2023-01-01 00:00:00')

                        -- If the search was updated or created more recently
                        -- than the last email, we'll include it
                        OR s.updated_at > u.last_received_email_at
                    )
                    AND (
                        -- Convert days to seconds and select users
                        -- who haven't received an email more recently than their
                        -- last email frequency period
                        -- In other words, if you want to receive an email every 7
                        -- days and it's been more than 7 days since you got an email
                        -- we should send you one
                        -- NOW() - last_received_email_at gives us the amount of time since
                        -- you last got an email.
                        -- If that's a bigger amount of time than your email frequency,
                        -- then we should send you an email.
                        EXTRACT(epoch FROM NOW() - COALESCE(u.last_received_email_at, '2023-01-01 00:00:00')) > (24 * 60 * 60 * u.email_frequency_days)
                        OR is_admin
                    )
                    AND NOT c.board_url_is_dead_link
                """
            )
        ).all()
        or []
    )


def generate_link_html(posting: Dict[str, str]) -> str:
    return f"""
        <li><a href="{posting.get('href')}">{posting.get('text')}</a></li>
    """


def generate_email_html(
    first_name: str, matching_postings: Dict[str, List[str]], email_frequency_days: int
) -> str:
    all_postings = {}

    ## Sort the keys so the email comes back in alphabetical order
    for company, jobs in {key: value for key, value in sorted(matching_postings.items())}.items():
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
        searches = {
            email: list(data)
            for email, data in groupby(get_user_job_searches(), attrgetter("email"))
        }

        for email, searches in searches.items():
            current_app.logger.info(f"Collecting relevant links for {email}")
            relevant_postings = filter(lambda x: is_matching_posting(x), searches)

            ads = list(
                map(
                    lambda x: {
                        "company_name": x.company_name,
                        "ad": create_posting_advertisement(x),
                    },
                    relevant_postings,
                )
            )

            companies = set(map(lambda x: x.get("company_name"), ads))

            links_by_company = {
                company: [
                    ad.get("ad") for ad in ads if ad.get("company_name") == company
                ]
                for company in companies
            }

            current_app.logger.info(
                f"Collected relevant links for {email}. Found the following postings {links_by_company}"
            )

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
                    current_app.logger.info(f"Sent email to {email}")
                    current_app.logger.info(
                        f"Updating last_received_email_at for {email}"
                    )

                    user = Users.query.filter_by(email=email).first()

                    user.last_received_email_at = datetime.datetime.now()
                    db.session.commit()

                    current_app.logger.info(
                        f"Updated last_received_email_at for {email}"
                    )
