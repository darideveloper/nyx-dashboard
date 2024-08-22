from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By


def get_selenium_elems(driver: webdriver, selectors: dict) -> dict[str, WebElement]:
    fields = {}
    for key, value in selectors.items():
        try:
            fields[key] = driver.find_element(By.CSS_SELECTOR, value)
        except Exception:
            fields[key] = None
    return fields