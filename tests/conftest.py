from jobcrawler import create_app, db
import pytest

@pytest.fixture
def app():
    app = create_app()

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
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

@pytest.fixture
def client__superuser(app):
    client = app.test_client()

    client.post(
        "/signup",
        data = {"email": 'mrkaye97@gmail.com', "password": 'superuser', "first_name": "matt"},
        content_type = 'application/x-www-form-urlencoded',
        follow_redirects = True
    )

    return client

