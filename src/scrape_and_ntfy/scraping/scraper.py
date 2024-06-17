from typing import OrderedDict, List
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
from scrape_and_ntfy.utils.logging import logger
from scrape_and_ntfy.utils.db import db
from scrape_and_ntfy.scraping.notifier import Notifier
from scrape_and_ntfy.utils import convert_to_float
import time

driver: webdriver.Chrome = None

# https://docs.sqlalchemy.org/en/20/core/type_basics.html


class UrlScraper:
    scrapers = []

    def __init__(
        self,
        url: str,
        css_selector: str,
        interval: int = 60,
        name: str = None,
        pause_time: int = 0,
        notifiers: List[Notifier] = [],
        scroll_to_bottom: bool = False,
    ):
        """
        Add a scraper to the database and the list of scrapers
        If a name is not provided, the name will be f"{url} ({css_selector})"
        A duplicate scraper will not be created if the URL, CSS selector, and name are the same. Thus, you can use name to differentiate between scrapers if you need multiple scrapers with the same URL, CSS selector.
        If you rename a scraper and then run the script, a new scraper will be created with an empty last_scrape and data. When the database is cleaned, the old scraper will be deleted.
        You can set pause_time to the number of seconds to wait between scrolling (if scroll_to_bottom is True) or, if scroll_to_bottom is False, the number of seconds to wait before attempting to find element.
        """
        self.notifiers = notifiers
        self.url = url
        self.css_selector = css_selector
        self.interval = interval
        # Set name to the URL and CSS selector if not provided
        self.name = name if name else f"{url} ({css_selector})"
        self.pause_time = pause_time
        self.scroll_to_bottom = scroll_to_bottom
        self._last_scrape = None
        # By default, an auto-incrementing primary key (id) is created
        table = db["scrapers"]
        id = table.insert_ignore(
            row={
                "url": self.url,
                "css_selector": self.css_selector,
                "interval": self.interval,
                "name": self.name,
                "pause_time": self.pause_time,
                "scroll_to_bottom": self.scroll_to_bottom,
                "last_scrape": self._last_scrape,
                "data": None,
            },
            keys=["url", "css_selector", "name"],
            # `ensure`, by default, is set to True so setting it to True is redundant
            # When set to True, it will create the columns if they don't exist, which is what we want
            ensure=True,
            types={
                "url": db.types.text,
                "css_selector": db.types.text,
                "interval": db.types.integer,
                "name": db.types.text,
                "pause_time": db.types.integer,
                "scroll_to_bottom": db.types.boolean,
                "last_scrape": db.types.float,
                "data": db.types.text,
            },
        )
        if id is False:
            id = table.find_one(
                url=self.url, css_selector=self.css_selector, name=self.name
            )["id"]
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
                logger.info(
                    f"Deleted scraper for {scraper['url']} with ID {scraper['id']}"
                )

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
        if scraper["scroll_to_bottom"]:
            # https://stackoverflow.com/a/27760083/
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                # Scroll down to bottom
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                # Wait to load page
                logger.debug(f"Waiting {scraper['pause_time']} seconds")
                time.sleep(scraper["pause_time"])
                logger.debug("Done waiting")

                # Calculate new scroll height and compare with last scroll height
                new_height = driver.execute_script("return document.body.scrollHeight")
                try:
                    element = driver.find_element(
                        webdriver.common.by.By.CSS_SELECTOR, scraper["css_selector"]
                    )
                except NoSuchElementException:
                    pass
                else:
                    # If the element is found, return the text
                    return element.text
                if new_height == last_height:
                    logger.debug("Reached bottom of page")
                    break
                last_height = new_height
        else:
            logger.debug(f"Waiting {scraper['pause_time']} seconds")
            time.sleep(scraper["pause_time"])
            logger.debug("Done waiting")
            try:
                element = driver.find_element(
                    webdriver.common.by.By.CSS_SELECTOR, scraper["css_selector"]
                )
            except NoSuchElementException:
                # The warning is logged after the return, not here
                return None
            else:
                return element.text
        return None

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
                    # If the new data is different from the old data, log it
                    if data is None:
                        if scraper["data"] is None and scraper["last_scrape"] is None:
                            message = f"{scraper["name"]} not found on first scrape"
                        else:
                            message = f"{scraper["name"]} not found"
                        cls.send_to_all_notifiers(
                            scraper, message, Notifier.NotifyOn.ERROR
                        )
                    elif scraper["data"] != data:
                        if scraper["data"] is None and scraper["last_scrape"] is None:
                            message = f"First scrape for {scraper["name"]} with data \"{data}\""
                            cls.send_to_all_notifiers(
                                scraper, message, Notifier.NotifyOn.FIRST_SCRAPE
                            )
                        else:
                            notification_event = Notifier.NotifyOn.CHANGE
                            # If the last data was a number and the new data is a number, compare them as numbers
                            # convert_to_float is used since it checks if the string is still a number after removing non-numeric characters
                            if isinstance(
                                convert_to_float(scraper["data"]), float
                            ) and isinstance(convert_to_float(data), float):
                                if convert_to_float(scraper["data"]) < convert_to_float(
                                    data
                                ):
                                    message = f"Value increased for {scraper["name"]} from \"{scraper["data"]}\" to \"{data}\""
                                    notification_event = Notifier.NotifyOn.NUMERIC_UP
                                elif convert_to_float(
                                    scraper["data"]
                                ) > convert_to_float(data):
                                    message = f"Value decreased for {scraper["name"]} from \"{scraper["data"]}\" to \"{data}\""
                                    notification_event = Notifier.NotifyOn.NUMERIC_DOWN
                                else:
                                    message = f"Value unchanged but data changed for {scraper["name"]} from \"{scraper["data"]}\" to \"{data}\""
                                    notification_event = Notifier.NotifyOn.NO_CHANGE
                            else:
                                message = f"Data changed for {scraper["name"]} from \"{scraper["data"]}\" to \"{data}\""
                            cls.send_to_all_notifiers(
                                scraper, message, notification_event
                            )
                    else:
                        message = (
                            f"Data unchanged for {scraper["name"]} with data \"{data}\""
                        )
                        cls.send_to_all_notifiers(
                            scraper, message, Notifier.NotifyOn.NO_CHANGE
                        )
                    scraper["last_scrape"] = datetime.now().timestamp()
                    scraper["data"] = data
                    db["scrapers"].update(scraper, ["id"])
            else:
                logger.debug(
                    f"Scraper with ID {scraper['id']} not in list of scrapers but in database; skipping"
                )

    @classmethod
    def send_to_all_notifiers(
        cls,
        scraper,
        message: str,
        notification_type: Notifier.NotifyOn = Notifier.NotifyOn.CHANGE,
    ):
        """
        Send the message to all notifiers
        """
        # Find the scraper from the database in the list of scrapers since the notifiers are stored in-memory
        for s in cls.scrapers:
            if s["id"] == scraper["id"]:
                scraper = s
                for notifier in scraper["notifiers"]:
                    if notification_type in notifier.notify_on:
                        notifier.notify(message)

                # Depending on the type, log the message with a different level
                if notification_type == Notifier.NotifyOn.ERROR:
                    logger.warning(message)
                elif (
                    notification_type == Notifier.NotifyOn.CHANGE
                    or notification_type == Notifier.NotifyOn.FIRST_SCRAPE
                    or notification_type == Notifier.NotifyOn.NUMERIC_UP
                    or notification_type == Notifier.NotifyOn.NUMERIC_DOWN
                ):
                    logger.info(message)
                elif notification_type == Notifier.NotifyOn.NO_CHANGE:
                    logger.debug(message)
                # If the type is in the enum but not implemented, log a error
                elif notification_type not in list(Notifier.NotifyOn):
                    logger.error(
                        f"Notifier notification_type {notification_type} not implemented"
                    )
                else:
                    logger.error(f"Unknown notifier type {notification_type}")
