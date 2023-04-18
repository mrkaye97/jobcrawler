from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
import sib_api_v3_sdk
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

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

    print(response)

def get_links_selenium(url, query, company):
    results = []
    DRIVER="geckodriver"
    service = Service(executable_path=DRIVER)
    driver = webdriver.Firefox(service=service)
    delay = 3

    driver.implicitly_wait(delay)
    driver.get(url)
    links =  driver.find_elements(By.XPATH, "//a[@href]")

    for link in links:
        text = link.get_attribute("text")
        href = link.get_attribute("href")

        if query.lower() in text.lower():
            results = results + [f"{text} @ {company}: {href}"]

    driver.quit()

    return results

def get_links_soup(url, query, company):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, features="html.parser")

    links = lambda tag: (getattr(tag, 'name', None) == 'a' and 'href' in tag.attrs and query.lower() in tag.get_text().lower())

    links = soup.find_all(links)

    results = []
    for link in links:
        href_parsed = urlparse(link.get("href"))
        search_parsed = urlparse(url)
        if search_parsed.path in href_parsed.path:
            job_title = link.string
            if 'lever' in url:
                job_title = link.contents[0].text
            results = results + [f"{job_title} @ {company}: {urljoin(url, link['href'])}"]

    return results
