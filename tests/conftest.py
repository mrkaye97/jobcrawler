from jobcrawler import create_app
import pytest

@pytest.fixture
def app():
    app = create_app()
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def client__logged_in(app):
    client = app.test_client()

    client.post(
        "/signup",
        data = {"email": 'j@bond.com', "password": '007', "first_name": "james"},
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

