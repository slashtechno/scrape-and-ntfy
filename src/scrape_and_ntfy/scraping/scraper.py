from typing import OrderedDict, List
from selenium import webdriver
from datetime import datetime
from scrape_and_ntfy.utils.logging import logger
from scrape_and_ntfy.utils.db import db
from scrape_and_ntfy.scraping.notifier import Notifier

driver: webdriver.Chrome = None

# https://docs.sqlalchemy.org/en/20/core/type_basics.html

class UrlScraper:
    scrapers = []

    def __init__(self, url: str, css_selector: str, interval: int, notifiers: List[Notifier] = []):
        self.notifiers = notifiers
        self.url = url
        self.css_selector = css_selector
        self.interval = interval
        self._last_scrape = None
        # By default, an auto-incrementing primary key (id) is created
        table = db["scrapers"]
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
        if id is False:
            id = table.find_one(url=self.url, css_selector=self.css_selector, interval=self.interval)["id"]
            logger.info(f"Found existing scraper for {self.url} with ID {id}")
        else:
            logger.info(f"Created scraper for {self.url} with ID {id}")
        self.scrapers.append(
            {
                "id": id,
                "url": self.url,
                "css_selector": self.css_selector,
                "interval": self.interval,
                "last_scrape": self._last_scrape,
                "notifiers": self.notifiers,
            }
        )
        self._id = id
    @property
    def id(self):
        """read-only id property"""
        return self._id
    @classmethod
    def clean_db(cls):
        """
        Remove all scrapers from the database that aren't in the list of scrapers
        """
        for scraper in db["scrapers"]:
            if scraper["id"] not in cls.scraper_ids():
                db["scrapers"].delete(id=scraper["id"])
                logger.info(f"Deleted scraper for {scraper['url']} with ID {scraper['id']}")
    @classmethod
    def scraper_ids(cls):
        """
        Get the IDs of the scrapers
        """
        return [scraper["id"] for scraper in cls.scrapers]
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

    @classmethod
    def scrape_all_urls(cls):
        """
        Scrape all URLs that have their interval met/exceeded (or have never been scraped and have a null last scrape)
        """
        # Not doing `for scraper in cls.scrapers` because we want to update the database and compare the data and last scrape time
        for scraper in db["scrapers"]:
            if scraper["id"] in cls.scraper_ids():
                if scraper["last_scrape"] is None or (
                    scraper["last_scrape"] + scraper["interval"]
                    <= datetime.now().timestamp()
                ):
                    data = UrlScraper.scrape_url(scraper)
                    # Add the data to the scraper in the DB
                    scraper["last_scrape"] = datetime.now().timestamp()
                    # If the new data is different from the old data, log it
                    # TODO: Make it so the conditions for notifying are configurable
                    if scraper["data"] != data:
                        if scraper["data"] is None:
                            logger.info(f"First scrape for {scraper['url']} with data {data}")
                            cls.send_to_all_notifiers(scraper, f"First scrape for {scraper['url']} with data {data}")
                        else:
                            logger.info(f"Data changed for {scraper['url']} from {scraper['data']} to {data}")
                            cls.send_to_all_notifiers(scraper, f"Data changed for {scraper['url']} from {scraper['data']} to {data}")
                    else:
                        logger.debug(f"Data unchanged for {scraper['url']} with data {data}")
                        cls.send_to_all_notifiers(scraper, f"Data unchanged for {scraper['url']} with data {data}")
                    scraper["data"] = data
                    db["scrapers"].update(scraper, ["id"])
            else:
                logger.debug(f"Scraper with ID {scraper['id']} not in list of scrapers but in database; skipping")
    @classmethod
    def send_to_all_notifiers(cls, scraper, message: str):
        """
        Send the message to all notifiers
        """
        # Find the scraper from the database in the list of scrapers since the notifiers are stored in-memory
        for s in cls.scrapers:
            if s["id"] == scraper["id"]:
                scraper = s
                for notifier in scraper["notifiers"]:
                    notifier.notify(message)