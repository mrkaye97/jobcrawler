from jobcrawler.jobs.scraping import load_page, create_posting_advertisement, is_matching_posting, get_users_to_email
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
