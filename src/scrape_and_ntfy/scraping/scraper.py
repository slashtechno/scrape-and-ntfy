import dataset
from selenium import webdriver

db: dataset.Database = None
driver: webdriver.Chrome = None


class UrlScraper:
    scrapers = []

    def __init__(self, url: str, css_selector: str, interval: int):
        self.url = url
        self.css_selector = css_selector
        self.interval = interval
        self._last_scrape = None

    @staticmethod
    def scrape_url(scraper):
        """
        Scrape the website
        """
        driver.get(scraper.url)
        element = driver.find_element(
            webdriver.common.by.By.CSS_SELECTOR, scraper.css_selector
        )
        # https://selenium-python.readthedocs.io/api.html#module-selenium.webdriver.remote.webelement
        return element.text
