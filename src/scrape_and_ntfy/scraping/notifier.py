import httpx
# from scrape_and_ntfy.utils.logging import logger
# from scrape_and_ntfy.utils.db import db

class Notifier:
    # notifiers = []
    @staticmethod
    def notify(*args, **kwargs):
        raise NotImplementedError("Subclasses must implement this method")

class Webhook(Notifier):
    def __init__(self, url):
        """
        Instantiate a webhook and ~~add the webhook to the database~~
        """
        self.url = url

        
    @property
    def id(self):
        return self._id
    # @staticmethod
    # def notify(url: str, message: str):
    def notify(self, message: str):
        """
        Notify the webhook
        """
        httpx.post(self.url, data={"content": message})