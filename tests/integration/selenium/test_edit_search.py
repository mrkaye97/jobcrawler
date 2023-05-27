import pytest
from jobcrawler.jobs.scraping import *
from selenium.webdriver.common.by import By
from flask import url_for
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
import time


def sign_up_and_log_in(driver):
    driver.find_element(
        By.XPATH, "/html/body/div/section/div[1]/nav/div/div[2]/a[1]"
    ).click()

    email = "j@bond.com"
    password = "007"

    ## Fill in login form
    driver.find_element(
        By.XPATH, "/html/body/div/section/div[2]/div/div/div/form/div[1]/div/input"
    ).send_keys(email)
    driver.find_element(
        By.XPATH, "/html/body/div/section/div[2]/div/div/div/form/div[2]/div/input"
    ).send_keys(password)
    driver.find_element(
        By.XPATH, "/html/body/div/section/div[2]/div/div/div/form/button"
    ).click()

    return driver


def create_search(driver, company, text):
    driver.find_element(By.XPATH, '//*[@id="add-row-btn"]').click()

    driver.implicitly_wait(10)
    modal = driver.find_element(By.CLASS_NAME, "modal-content")

    WebDriverWait(modal, 20).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="search-text"]'))
    ).send_keys(text)
    select = Select(driver.find_element(By.XPATH, '//*[@id="company-name"]'))
    select.select_by_visible_text(company)

    time.sleep(0.25)

    modal.find_element(By.XPATH, '//*[@id="save-row-btn"]').click()


@pytest.mark.usefixtures("live_server")
def test_editing_cards(client__logged_in):
    driver = create_driver()

    url = url_for("searches_bp.get_searches", _external=True)
    driver.get(url)

    sign_up_and_log_in(driver)

    driver.find_element(
        By.CSS_SELECTOR,
        "body > div > section > div.hero-head > nav > div > div.d-flex.mr-auto > a:nth-child(3)",
    ).click()

    initial_cards = [
        {"company": "Foo", "search_regex": "data"},
        {"company": "Bar", "search_regex": "product"},
        {"company": "Baz", "search_regex": "software"},
    ]

    for c in initial_cards:
        create_search(driver, c["company"], c["search_regex"])
        time.sleep(0.25)

    cards_found = driver.find_elements(By.XPATH, '//*[@id="searches-container"]/div')

    assert len(cards_found) == len(initial_cards)

    actual_cards = []
    for i in range(len(cards_found)):
        actual_cards = actual_cards + [
            {
                "company": driver.find_element(
                    By.XPATH, f'//*[@id="searches-container"]/div[{i + 1}]/div/h5'
                ).text,
                "search_regex": driver.find_element(
                    By.XPATH, f'//*[@id="searches-container"]/div[{i + 1}]/div/p'
                ).text,
            }
        ]

    assert initial_cards == actual_cards

    driver.find_element(By.XPATH, '//*[@id="searches-container"]/div[2]/div').click()
    driver.implicitly_wait(10)
    middle_card_edit_modal = driver.find_element(By.CLASS_NAME, "modal-content")

    new_search_regex = "new search"
    WebDriverWait(middle_card_edit_modal, 20).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="search-text"]'))
    ).clear()
    WebDriverWait(middle_card_edit_modal, 20).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="search-text"]'))
    ).send_keys(new_search_regex)

    time.sleep(0.25)

    middle_card_edit_modal.find_element(By.XPATH, '//*[@id="save-row-btn"]').click()

    initial_cards[1] = {
        "company": initial_cards[1]["company"],
        "search_regex": new_search_regex,
    }

    cards_found = driver.find_elements(By.XPATH, '//*[@id="searches-container"]/div')

    actual_cards = []
    for i in range(len(cards_found)):
        actual_cards = actual_cards + [
            {
                "company": driver.find_element(
                    By.XPATH, f'//*[@id="searches-container"]/div[{i + 1}]/div/h5'
                ).text,
                "search_regex": driver.find_element(
                    By.XPATH, f'//*[@id="searches-container"]/div[{i + 1}]/div/p'
                ).text,
            }
        ]

    assert initial_cards == actual_cards

    driver.find_element(By.XPATH, '//*[@id="searches-container"]/div[2]/div').click()
    driver.implicitly_wait(10)
    middle_card_edit_modal = driver.find_element(By.CLASS_NAME, "modal-content")

    time.sleep(0.25)

    middle_card_edit_modal.find_element(By.XPATH, '//*[@id="delete-row-btn"]').click()

    time.sleep(0.25)

    cards_found = driver.find_elements(By.XPATH, '//*[@id="searches-container"]/div')

    assert len(cards_found) == 2
