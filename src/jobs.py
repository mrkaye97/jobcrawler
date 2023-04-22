from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
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

def get_links_selenium(url):
    DRIVER="geckodriver"
    service = Service(executable_path=DRIVER)
    driver = webdriver.Chrome(service=service)
    delay = 3

    driver.implicitly_wait(delay)
    driver.get(url)
    links =  driver.find_elements(By.XPATH, "//a[@href]")

    driver.quit()

    return [
        {
            "text": link.get_attribute("text"),
            "href": link.get_attribute("href")
        }
        for link in links
    ]

def get_links_soup(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, features="html.parser")

    links = lambda tag: (getattr(tag, 'name', None) == 'a' and 'href' in tag.attrs)

    links = soup.find_all(links)

    return [
        {
            "text": link.contents[0].text if 'lever' in url else link.string,
            "href": urlparse(link.get("href"))
        }
        for link in links
    ]
