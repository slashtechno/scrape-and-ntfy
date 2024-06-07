import httpx
from scrape_and_ntfy.utils.logging import logger
from scrape_and_ntfy.utils.db import db

class Notifier:
    notifiers = []
    @staticmethod
    def notify(*args, **kwargs):
        raise NotImplementedError("Subclasses must implement this method")
    @classmethod
    def clean_db(cls):
        """
        Remove all notifiers from the database that aren't in the list of notifiers
        """
        # for subclass in cls.__subclasses__():
        #     subclass.clean_db()
        for notifier in db["notifiers"]:
            if notifier["id"] not in cls.notifiers:
                db["notifiers"].delete(id=notifier["id"])
                logger.info(f"Deleted notifier for {notifier['url']} with ID {notifier['id']}")

class Webhook(Notifier):
    def __init__(self, url):
        """
        Add the webhook to the database
        """
        self.url = url
        table = db["notifiers"]
        self._id = table.insert(
            row={
                "url": self.url,
                "type": "webhook",
            },
            types={
                "url": db.types.text,
                "type": db.types.text,
            },
            ensure=True,
        )
        logger.info(f"Created webhook for {self.url} with ID {self._id}")
        # This updates the list of notifiers for all Notfier subclasses
        self.notifiers.append(self._id)
        
    @property
    def id(self):
        # return db["notifiers"].find_one(url=self.url, type="webhook")["id"]
        return self._id
    @staticmethod
    def notify(url: str, message: str):
        """
        Notify the webhook
        """
        httpx.post(url, data={"content": message})