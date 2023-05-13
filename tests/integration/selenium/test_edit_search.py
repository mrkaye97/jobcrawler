def test_homepage_aliases(client):
    landing = client.get("/")

    assert client.get("/index").data == landing.data

def test_homepage_loads_correctly(client):
    landing = client.get("/")
    html = landing.data.decode()

    # Check that link to home page exists
    assert "<a href=\"/index\" class=\"btn btn-outline-primary me-2\">Home</a>" in html
    assert "<a href=\"/login\" class=\"btn btn-outline-primary me-2\">Login</a>" in html

    assert "Preferences" not in html
    assert "Companies" in html

    assert landing.status_code == 200

def test_buttons_intended_for_logged_in_dont_load(client__logged_in):
    landing = client__logged_in.get("/")

    html = landing.data.decode()
    html = "".join(html.split())

    ## Preferences and Logout buttons should only show for logged-in users
    assert "<ahref=\"/preferences\"class=\"btnbtn-outline-primaryme-2\">Preferences</a>" in html
    assert "<ahref=\"/logout\"class=\"btnbtn-outline-primary\">Logout</a>" in html

    ## Login should not show up for logged-in users
    assert "<a href=\"/login\"class=\"btn btn-outline-primaryme-2\">Login</a>" not in html
