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
        interval: int,
        verbose_notifications: bool = False,
        notifiers: List[Notifier] = [],
        scroll_to_bottom: bool = False,
    ):
        self.notifiers = notifiers
        self.url = url
        self.css_selector = css_selector
        self.interval = interval
        self.verbose_notifications = verbose_notifications
        self.scroll_to_bottom = scroll_to_bottom
        self._last_scrape = None
        # By default, an auto-incrementing primary key (id) is created
        table = db["scrapers"]
        id = table.insert_ignore(
            row={
                "url": self.url,
                "css_selector": self.css_selector,
                "interval": self.interval,
                # Verbose notifications and scroll to bottom really don't need to be in the database
                # But otherwise more code would need to be added to search for the scraper in the list of scrapers from the db entry
                "verbose_notifications": self.verbose_notifications,
                "scroll_to_bottom": self.scroll_to_bottom,
                "last_scrape": self._last_scrape,
                "data": None,
            },
            keys=["url", "css_selector", "interval"],
            # `ensure`, by default, is set to True so setting it to True is redundant
            # When set to True, it will create the columns if they don't exist, which is what we want
            ensure=True,
            types={
                "url": db.types.text,
                "css_selector": db.types.text,
                "interval": db.types.integer,
                "verbose_notifications": db.types.boolean,
                "scroll_to_bottom": db.types.boolean,
                "last_scrape": db.types.float,
                "data": db.types.text,
            },
        )
        if id is False:
            id = table.find_one(
                url=self.url, css_selector=self.css_selector, interval=self.interval
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
            # TODO: Add a "max time" that dictates how long the scraper will spend scrolling. Perhaps also add an option for SCROLL_PAUSE_TIME then
            # https://stackoverflow.com/a/27760083/
            SCROLL_PAUSE_TIME = 3
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                # Scroll down to bottom
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                # Wait to load page
                time.sleep(SCROLL_PAUSE_TIME)

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
                    break
                last_height = new_height
        else:
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
        # TODO: Instead of URL and class name make an alias that defaults to the URL and class name
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
                            message = f"CSS selector \"{scraper['css_selector']}\" for {scraper['url']} not found on first scrape"
                        else:
                            message = f"CSS selector \"{scraper['css_selector']}\" for {scraper['url']} not found"
                        cls.send_to_all_notifiers(
                            scraper, message, Notifier.NotifyOn.ERROR
                        )
                    elif scraper["data"] != data:
                        if scraper["data"] is None and scraper["last_scrape"] is None:
                            message = f"First scrape for {scraper['url']} with data \"{data}\""
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
                                    message = f"Value increased{(f' for {scraper['url']}' if scraper["verbose_notifications"] else '')} from \"{scraper['data']}\" to \"{data}\""
                                    # message = f"Value increased {scraper['url']} from \"{scraper['data']}\" to \"{data}\""
                                    notification_event = Notifier.NotifyOn.NUMERIC_UP
                                elif convert_to_float(
                                    scraper["data"]
                                ) > convert_to_float(data):
                                    message = f"Value decreased{(f' for {scraper['url']}' if scraper["verbose_notifications"] else '')} from \"{scraper['data']}\" to \"{data}\""
                                    notification_event = Notifier.NotifyOn.NUMERIC_DOWN
                                else:
                                    message = f"Value unchanged but data changed{(f' for {scraper['url']}' if scraper["verbose_notifications"] else '')} from \"{scraper['data']}\" to \"{data}\""
                                    notification_event = Notifier.NotifyOn.NO_CHANGE
                            else:
                                message = f"Data changed{(f' for {scraper['url']}' if scraper["verbose_notifications"] else '')} from \"{scraper['data']}\" to \"{data}\""
                            cls.send_to_all_notifiers(
                                scraper, message, notification_event
                            )
                    else:
                        message = f"Data unchanged {(f' for {scraper['url']}' if scraper["verbose_notifications"] else '')} with data \"{data}\""
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
