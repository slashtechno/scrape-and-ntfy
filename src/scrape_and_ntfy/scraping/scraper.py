from typing import OrderedDict
import dataset
from selenium import webdriver
from datetime import datetime
from scrape_and_ntfy.utils.logging import logger

db: dataset.Database
driver: webdriver.Chrome = None

# https://docs.sqlalchemy.org/en/20/core/type_basics.html

class UrlScraper:
    global db
    scrapers = []

    def __init__(self, url: str, css_selector: str, interval: int):
        self.url = url
        self.css_selector = css_selector
        self.interval = interval
        self._last_scrape = None
        # By default, an auto-incrementing primary key (id) is created
        table = db["scrapers"]
        # TODO: This could probably be simplified by just using insert as clean_db should remove anything the user didn't instantiate. However, this would assume that the user didn't add any duplicates. I don't think that's too much of a concern, but it's something to consider.
        id = table.insert_ignore(
            row={
                "url": self.url,
                "css_selector": self.css_selector,
                "interval": self.interval,
                "last_scrape": self._last_scrape,
            },
            keys=["url", "css_selector", "interval"],
            # `ensure`, by default, is set to True so setting it to True is redundant
            # When set to True, it will create the columns if they don't exist, which is what we want
            ensure=True,
            types={
                "url": db.types.text,
                "css_selector": db.types.text,
                "interval": db.types.integer,
                "last_scrape": db.types.float,
            },
        )
        # TODO: Check if the ID was added. If it wasn't, get the ID from the existing row
        if id is False:
            id = table.find_one(url=self.url, css_selector=self.css_selector, interval=self.interval)["id"]
            logger.info(f"Found existing scraper for {self.url} with ID {id}")
        else:
            logger.info(f"Created scraper for {self.url} with ID {id}")
        self.scrapers.append(id)

    @staticmethod
    def clean_db():
        """
        Remove all scrapers from the database that aren't in the list of scrapers
        """
        for scraper in db["scrapers"]:
            if scraper["id"] not in UrlScraper.scrapers:
                db["scrapers"].delete(id=scraper["id"])
                logger.info(f"Deleted scraper for {scraper['url']} with ID {scraper['id']}")
    @staticmethod
    # As of Python 3.7 dicts are ordered by default
    # But technically it seems that dataset uses OrderedDicts (probably for backwards compatibility)
    def scrape_url(scraper: OrderedDict):
        """
        Scrape the website
        """
        driver.get(scraper["url"])
        element = driver.find_element(
            webdriver.common.by.By.CSS_SELECTOR, scraper["css_selector"]
        )
        # https://selenium-python.readthedocs.io/api.html#module-selenium.webdriver.remote.webelement
        return element.text

    @staticmethod
    def scrape_all_urls():
        """
        Scrape all URLs that have their interval met/exceeded (or have never been scraped and have a null last scrape)
        """
        for scraper in db["scrapers"]:
            if scraper["last_scrape"] is None or (
                scraper["last_scrape"] + scraper["interval"]
                <= datetime.now().timestamp()
            ):
                data = UrlScraper.scrape_url(scraper)
                # Add the data to the scraper in the DB
                scraper["last_scrape"] = datetime.now().timestamp()
                # If the new data is different from the old data, log it
                if scraper["data"] != data:
                    if scraper["data"] is None:
                        logger.info(f"First scrape for {scraper['url']} with data {data}")
                    else:
                        logger.info(f"Data changed for {scraper['url']} from {scraper['data']} to {data}")
                else:
                    logger.debug(f"Data unchanged for {scraper['url']} with data {data}")
                scraper["data"] = data
                db["scrapers"].update(scraper, ["id"])