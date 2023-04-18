from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import sib_api_v3_sdk
import os

app = Flask(__name__)

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

# function to add profiles
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

@sched.scheduled_job(trigger = 'interval', seconds = 3, id='crawl')
def crawl():
    """ Function for test purposes. """
    print("Scheduler is alive!")
    results = []
    with app.app_context():
        searches = db.session.query(Boards.company, Boards.url, Boards.search_text)

        for search in searches:
            r = requests.get(search.url)
            soup = BeautifulSoup(r.content, features="html.parser")

            print(search.search_text.lower())
            links = lambda tag: (getattr(tag, 'name', None) == 'a' and
                                    'href' in tag.attrs and
                                    search.search_text.lower() in tag.get_text().lower())

            links = soup.find_all(links)
            links = [urljoin(search.url, tag['href']) for tag in links]

            if links:
                links = ", ".join(links)
                links = [f"{search.company} -- {search.search_text}: {links}"]
                results = results + links

    result_txt = "\n".join(results)
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

sched.start()

if __name__ == '__main__':
    app.run()


