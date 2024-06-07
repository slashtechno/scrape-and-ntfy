import httpx
from typing import List
from enum import Enum
# from scrape_and_ntfy.utils.logging import logger
# from scrape_and_ntfy.utils.db import db

class Notifier:
    # notifiers = []
    @staticmethod
    def notify(*args, **kwargs):
        raise NotImplementedError("Subclasses must implement this method")
    class NotifyOn(Enum):
        """
        Enum to specify when to notify
        """
        CHANGE = "change"
        FIRST_SCRAPE = "first_scrape"
        NO_CHANGE = "no_change"
        ERROR = "error"

class Webhook(Notifier):
    def __init__(self, url: str, notify_on: List[Notifier.NotifyOn] = [Notifier.NotifyOn.CHANGE, Notifier.NotifyOn.FIRST_SCRAPE, Notifier.NotifyOn.NO_CHANGE, Notifier.NotifyOn.ERROR]):
        """
        Instantiate a webhook and ~~add the webhook to the database~~
        """
        self.url = url
        self.notify_on = notify_on

        
    # @property
    # def id(self):
    #     return self._id
    # @staticmethod
    # def notify(url: str, message: str):
    def notify(self, message: str):
        """
        Notify the webhook
        """
        httpx.post(self.url, data={"content": message})