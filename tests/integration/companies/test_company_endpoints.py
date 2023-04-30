import json

def test_getting_companies_returns_correct_keys(client):
    resp = client.get("/companies")

    for company in json.loads(resp.data):
        assert set(company.keys()) == {"board_url", "id", "job_posting_url_prefix", "name", "scraping_method"}

def test_creating_new_company(client):
    data = {
        "name": "Foo",
        "board_url": "https://bar.com",
        "job_posting_url_prefix": "https://bar.com/jobs",
        "scraping_method": "selenium"
    }

    company = client.post(
        "/companies",
        data = json.dumps(data),
        content_type='application/json'
    )

    response = json.loads(company.data.decode('utf8'))
    for k, v in data.items():
        assert response.get(k)
        assert response.get(k) == v

    assert response.get("id")
