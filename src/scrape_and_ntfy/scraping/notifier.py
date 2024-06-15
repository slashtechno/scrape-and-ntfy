import httpx
from typing import List, Literal, Dict
from enum import Enum
from scrape_and_ntfy.utils.logging import logger
import json
# from scrape_and_ntfy.utils.db import db


class Notifier:
    # notifiers = []
    class NotifyOn(Enum):
        """
        Enum to specify when to notify
        """

        CHANGE = "change"
        FIRST_SCRAPE = "first_scrape"
        NO_CHANGE = "no_change"
        ERROR = "error"
        # That can be used for prices or other numeric values
        NUMERIC_UP = "numeric_up"
        NUMERIC_DOWN = "numeric_down"

    @staticmethod
    def notify(*args, **kwargs):
        raise NotImplementedError("Subclasses must implement this method")

    SUB_NOTIFICATION_EVENTS = {
        NotifyOn.CHANGE: [NotifyOn.NUMERIC_UP, NotifyOn.NUMERIC_DOWN],
    }

    @property
    def notify_on(self):
        return self._notify_on

    @notify_on.setter
    def notify_on(self, notify_on):
        self._notify_on = self.include_sub_notify_events(
            notify_on=notify_on, sub_notify_on=self.SUB_NOTIFICATION_EVENTS
        )

    @staticmethod
    def include_sub_notify_events(
        notify_on: List[NotifyOn],
        sub_notify_on: Dict[NotifyOn, List[NotifyOn]] = SUB_NOTIFICATION_EVENTS,
    ):
        """
        When an event such as CHANGE is specified also include the sub-events such as NUMERIC_UP and NUMERIC_DOWN
        """
        for event in notify_on:
            if event in sub_notify_on.keys():
                notify_on.extend(sub_notify_on[event])
                logger.debug(
                    f"Added sub-notifications ({sub_notify_on[event]}) for event {event}"
                )
        return notify_on


class Webhook(Notifier):
    def __init__(
        self,
        url: str,
        content_field: str = "content",
        notify_on: List[Notifier.NotifyOn] = [
            no.name for no in list(Notifier.NotifyOn)
        ],
    ):
        """
        Instantiate a webhook and ~~add the webhook to the database~~
        """
        self.url = url
        self.notify_on = notify_on
        self.content_field = content_field

    # @property
    # def id(self):
    #     return self._id
    # @staticmethod
    # def notify(url: str, message: str):
    def notify(self, message: str):
        """
        Notify the webhook
        """
        resp = httpx.post(
            self.url,
            headers={"Content-Type": "application/json"},
            data=json.dumps({self.content_field: message}),
        )
        logger.debug(
            f"Webhook text response: {resp.text} | status code: {resp.status_code}"
        )


class Ntfy(Notifier):
    def __init__(
        self,
        url: str,
        notify_on: List[Notifier.NotifyOn] = [
            no.name for no in list(Notifier.NotifyOn)
        ],
        on_click: str = None,
        priority: Literal[1, 2, 3, 4, 5] = "default",
        tags: str = None,
    ):
        """
        Instantiate a Ntfy notifier
        For information on the parameters, see https://docs.ntfy.sh/publish/
        """
        # Not sure if I should handle checking for None here or in notify()
        self.url = url
        self.notify_on = notify_on
        self.on_click = on_click
        self.priority = priority
        self.tags = tags

    def notify(self, message: str):
        """
        Notify the Ntfy endpoint
        """
        # Set headers
        headers = {
            # "Content-Type": "application/json",
        }
        if self.on_click:
            headers["Click"] = self.on_click
        if self.priority:
            headers["Priority"] = str(self.priority)
        if self.tags:
            headers["Tags"] = self.tags
        # Send the request
        httpx.post(self.url, data=message.encode("utf-8"), headers=headers)
