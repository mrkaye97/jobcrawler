from jobcrawler.jobs.scraping import *
from jobcrawler.exceptions import ScrapingException
from jobcrawler import db
import pytest

from jobcrawler.models.users import Users

def test_load_page_raises_on_404():
    with pytest.raises(ScrapingException):
        load_page("https://matthewrkaye.com/foobarbaz")

def test_load_page_works_for_existing():
    r = load_page("https://matthewrkaye.com")

    ## Check that my about page is loaded correctly
    assert "Matt" in r.text
    assert "Strava" in r.text

def test_matching_postings():
    assert is_matching_posting("foobar", "bazfoobarqux")
    assert not is_matching_posting("foo", "bazqux")

    assert is_matching_posting("(foo|bar)", "barbazqux")
    assert not is_matching_posting("(foo|bar)", "bazqux")

    assert is_matching_posting("(senior )?data scientist", "data scientist")
    assert is_matching_posting("(senior )?data scientist", "senior data scientist")

    ## Missing regex or text always returns False
    assert not is_matching_posting(None, "bazqux")
    assert not is_matching_posting("bazqux", None)
    assert not is_matching_posting(None, None)

def test_posting_ad_creation():
    title = "foo bar"
    company = "baz"
    href = "qux.com"

    ad = create_posting_advertisement(title, company, href)

    assert title in ad.get("text")
    assert "@" in ad.get("text")
    assert company in ad.get("text")
    assert href == ad.get("href")

def test_users_to_email(app):
    u1 = Users(email = "kaye.dev", email_frequency_days = 1)
    u2 = Users(email = "mk.dev", email_frequency_days = 1000000)

    db.session.add(u1)
    db.session.add(u2)
    db.session.commit()

    emails = [u.email for u in get_users_to_email()]

    assert "kaye.dev" in emails
    assert "mk.dev" not in emails

    db.session.delete(u1)
    db.session.delete(u2)

    db.session.commit()

def test_selenium_link_collection(app):
    from selenium import webdriver

    driver = webdriver.Chrome(options=set_chrome_options())

    links = get_links_selenium(driver, "https://matthewrkaye.com", "https://matthewrkaye.com")

    hrefs = [l.get("href") for l in links]
    texts = [l.get("text").strip() for l in links]

    assert "Matt Kaye" in texts
    assert "Blog" in texts
    assert "Code" in texts

    assert "https://matthewrkaye.com/" in hrefs
    assert "https://matthewrkaye.com/posts.html" in hrefs

    driver.quit()

def test_selenium_link_prefixing(app):
    from selenium import webdriver

    driver = webdriver.Chrome(options=set_chrome_options())

    links = get_links_selenium(driver, "https://matthewrkaye.com", "https://matthewrkaye.com/blog")

    hrefs = [l.get("href") for l in links]

    assert "https://matthewrkaye.com/" not in hrefs
    assert "https://matthewrkaye.com/blogroll.html" in hrefs

    driver.quit()

def test_soup_link_collection(app):
    links = get_links_soup("https://matthewrkaye.com", "https://")

    hrefs = [l.get("href") for l in links]
    texts = [l.get("text").strip() if l.get("text") else None for l in links]

    assert "Cookie Preferences" in texts
    assert "Quarto" in texts

    assert "https://www.strava.com/athletes/16125633" in hrefs
    assert "https://app.thestorygraph.com/profile/mrkaye97" in hrefs

def test_soup_link_prefixing(app):
    links = get_links_soup("https://matthewrkaye.com", "https://www.strava.com")

    hrefs = [l.get("href") for l in links]

    assert "https://www.strava.com/athletes/16125633" in hrefs
    assert "https://app.thestorygraph.com/profile/mrkaye97" not in hrefs
