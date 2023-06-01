from jobcrawler.jobs.scraping import *
from jobcrawler.jobs.email import *
from jobcrawler import db

from jobcrawler.models.users import Users
from jobcrawler.models.postings import Postings
from jobcrawler.models.searches import Searches
from jobcrawler.models.companies import Companies

from collections import namedtuple


def test_load_page_404s():
    response = load_page("https://matthewrkaye.com/foobarbaz")
    assert response.status_code == 404


def test_load_page_works_for_existing():
    r = load_page("https://matthewrkaye.com")

    ## Check that my about page is loaded correctly
    assert "Matt" in r.text
    assert "Strava" in r.text


def test_matching_postings():
    Search = namedtuple("Search", "search_regex link_text")

    assert is_matching_posting(Search("foobar", "bazfoobarqux"))
    assert not is_matching_posting(Search("foo", "bazqux"))

    assert is_matching_posting(Search("(foo|bar)", "barbazqux"))
    assert not is_matching_posting(Search("(foo|bar)", "bazqux"))

    assert is_matching_posting(Search("(senior )?data scientist", "data scientist"))
    assert is_matching_posting(
        Search("(senior )?data scientist", "senior data scientist")
    )

    ## Missing regex or text always returns False
    assert not is_matching_posting(Search(None, "bazqux"))
    assert not is_matching_posting(Search("bazqux", None))
    assert not is_matching_posting(Search(None, None))


def test_posting_ad_creation():
    Search = namedtuple("Search", "link_href link_text")

    title = "foo bar"
    href = "qux.com"

    ad = create_posting_advertisement(Search(href, title))

    assert title in ad.get("text")
    assert href == ad.get("href")


def test_users_to_email(app):
    c1 = Companies(
        name="test",
        board_url="test.com",
        job_posting_url_prefix="test.com",
        scraping_method="soup",
    )
    db.session.add(c1)

    ## Last received an email four days ago
    last_received_email_at = datetime.datetime.now() - datetime.timedelta(days=4)
    u1 = Users(
        email="kaye.dev",
        email_frequency_days=1,
        last_received_email_at=last_received_email_at,
    )
    u2 = Users(
        email="mk.dev",
        email_frequency_days=1000,
        last_received_email_at=last_received_email_at,
    )
    db.session.add(u1)
    db.session.add(u2)

    p1 = Postings(
        company_id=1,
        link_text="foo",
        link_href="bar",
        created_at=datetime.datetime.now() - datetime.timedelta(days=3),
    )
    db.session.add(p1)

    db.session.commit()

    s1 = Searches(company_id=1, search_regex="foo", user_id=1)
    s2 = Searches(company_id=1, search_regex="foo", user_id=2)
    db.session.add(s1)
    db.session.add(s2)
    db.session.commit()

    emails = [s.email for s in get_user_job_searches()]
    assert "kaye.dev" in emails
    assert "mk.dev" not in emails

    ## Unwind
    db.session.delete(s1)
    db.session.delete(s2)

    db.session.delete(p1)

    db.session.delete(u1)
    db.session.delete(u2)

    db.session.delete(c1)

    db.session.commit()


def test_selenium_link_collection(app):
    driver = create_driver()

    links = get_links_selenium(
        driver, "https://matthewrkaye.com", "https://matthewrkaye.com"
    )

    hrefs = [l.get("href") for l in links]
    texts = [l.get("text").strip() for l in links]

    assert "Matt Kaye" in texts
    assert "Blog" in texts
    assert "Code" in texts

    assert "https://matthewrkaye.com/" in hrefs
    assert "https://matthewrkaye.com/posts.html" in hrefs

    driver.quit()


def test_selenium_link_prefixing(app):
    driver = create_driver()

    links = get_links_selenium(
        driver, "https://matthewrkaye.com", "https://matthewrkaye.com/blog"
    )

    hrefs = [l.get("href") for l in links]

    assert "https://matthewrkaye.com/" not in hrefs
    assert "https://matthewrkaye.com/blogroll.html" in hrefs

    driver.quit()


def test_soup_link_collection(app):
    links = get_links_soup("https://matthewrkaye.com", "https://")

    hrefs = [l.get("href") for l in links]
    texts = [l.get("text").strip() if l.get("text") else None for l in links]

    assert "Strava" in texts
    assert "StoryGraph" in texts

    assert "https://www.strava.com/athletes/16125633" in hrefs
    assert "https://app.thestorygraph.com/profile/mrkaye97" in hrefs


def test_soup_link_prefixing(app):
    links = get_links_soup("https://matthewrkaye.com", "https://www.strava.com")

    hrefs = [l.get("href") for l in links]

    assert "https://www.strava.com/athletes/16125633" in hrefs
    assert "https://app.thestorygraph.com/profile/mrkaye97" not in hrefs


def test_soup_greenhouse(app):
    links = get_links_soup(
        "https://boards.greenhouse.io/collegevine",
        "https://boards.greenhouse.io/collegevine",
    )

    hrefs = [l.get("href") for l in links]

    assert not hrefs or "collegevine" in hrefs[0]


def test_soup_lever(app):
    links = get_links_soup(
        "https://jobs.lever.co/matchgroup", "https://jobs.lever.co/matchgroup"
    )

    hrefs = [l.get("href") for l in links]

    assert not hrefs or "https://jobs.lever.co/matchgroup" in hrefs[0]
