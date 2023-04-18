from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.sql import text
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
import sib_api_v3_sdk
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

template_dir = os.path.abspath('templates')
print(template_dir)
app = Flask(__name__, template_folder=template_dir)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/jobcrawler'

db = SQLAlchemy(app)

migrate = Migrate(app, db)

class Boards(db.Model):
    __table_args__ = (
        db.UniqueConstraint('company', 'url', 'search_text'),
    )

    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(256), unique=False, nullable=False)
    url = db.Column(db.String(256), unique=False, nullable=False)
    search_text = db.Column(db.String(256), unique=False, nullable=False)

    # repr method represents how one object of this datatable
    # will look like
    def __repr__(self):
        return f"Company : {self.company}, URL: {self.url}, search: {self.search_text}"


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/getjobs")
def getjobs():
    result = Boards.query.all()
    out = [{key: b.__dict__[key] for key in ["company", "url", "search_text"]} for b in result]
    print(out)
    return jsonify(out)

@app.route('/create', methods=["POST"])
def create():
    company = request.form.get("company")
    url = request.form.get("url")
    search_text = request.form.get("search_text")

    if company and url and search_text:
        p = Boards(company = company, url = url, search_text = search_text)
        db.session.add(p)
        db.session.commit()
        return jsonify(f"Successfully created {company} board @ {url}")
    else:
        return jsonify("Failed")

@app.route('/delete/<int:id>')
def erase(id):
    data = Boards.query.get(id)
    db.session.delete(data)
    db.session.commit()
    return jsonify(f"Successfully deleted {id}")

sched = BackgroundScheduler()

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

@sched.scheduled_job(trigger = 'interval', hours = 3, id='crawl')
def crawl():
    """ Function for test purposes. """
    print("Scheduler is alive!")
    results = []

    with app.app_context():
        searches = db.session.query(Boards.company, Boards.url, Boards.search_text)

        for search in searches:
            if search.company in ['Headspace']:
                results = results + get_links_selenium(url = search.url, query = search.search_text, company = search.company)
            else:
                results = results + get_links_soup(url = search.url, query = search.search_text, company = search.company)

    result_txt = "\n".join(results)

    if os.environ.get("PRODUCTION") == True:
        send_email(
            sender_email = "mrkaye97@gmail.com",
            sender_name = "Matt Kaye",
            recipient = "matt.kaye@collegevine.com",
            subject = "Your daily job feed digest",
            body = f"""
                Here are your links for the day!

                {result_txt}
            """
        )
    else:
        print(result_txt)

sched.start()

if __name__ == '__main__':
    app.run()
