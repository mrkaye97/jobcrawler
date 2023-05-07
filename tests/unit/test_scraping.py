from jobcrawler.jobs.scraping import load_page, create_posting_advertisement, is_matching_posting
from jobcrawler.exceptions import ScrapingException
import pytest

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

    assert title in ad
    assert "@" in ad
    assert company in ad
    assert href in ad
