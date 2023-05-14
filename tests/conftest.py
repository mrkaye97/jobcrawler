from jobcrawler import create_app, db
from jobcrawler.models.companies import Companies
import pytest
import multiprocessing

multiprocessing.set_start_method("fork")

@pytest.fixture(scope="session")
def app():
    app = create_app()

    with app.app_context():
        db.create_all()

        def create_record(name):
            record = Companies(
                name = name,
                board_url = "https://example.com",
                job_posting_url_prefix = "https://example.com",
                scraping_method = "soup"
            )

            db.session.add(record)

        for n in ["Foo", "Bar", "Baz", "Qux"]:
            create_record(n)

        db.session.commit()


    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()

@pytest.fixture(scope="session")
def client__logged_in(app):
    client = app.test_client()

    email = 'j@bond.com'
    password = "007"

    client.post(
        "/signup",
        data = {"email": email, "password": password, "first_name": "james"},
        content_type = 'application/x-www-form-urlencoded',
        follow_redirects = True
    )

    client.post(
        "/login",
        data = {"email": email, "password": password},
        content_type = 'application/x-www-form-urlencoded',
        follow_redirects = True
    )

    return client

