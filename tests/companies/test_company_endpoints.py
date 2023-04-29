import json

def test_getting_companies_returns_correct_keys(app):
    client = app.test_client()

    resp = client.get("/companies")

    for company in json.loads(resp.data):
        assert set(company.keys()) == {"board_url", "id", "job_posting_url_prefix", "name", "scraping_method"}

