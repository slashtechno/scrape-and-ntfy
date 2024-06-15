from scrape_and_ntfy.utils.logging import logger
from scrape_and_ntfy.utils.cli_args import args
from scrape_and_ntfy.scraping import scraper, UrlScraper
from scrape_and_ntfy.scraping import notifier
import selenium
import sys
import toml


def main():
    logger.debug(f"Args: {args}")
    try:
        config = toml.load(args.path_to_toml)
    except FileNotFoundError:
        logger.critical(f"File {args.path_to_toml} not found")
        sys.exit(1)
    if args.browser == "chrome" or args.browser == "chromium":
        options = selenium.webdriver.ChromeOptions()
        if args.headless:
            # If headless_path is set, use the binary at that path
            logger.info("Using Chrome headless")
            options.add_argument("--headless")
        else:
            logger.info("Not using headlessly")
        options.binary_location = args.browser_path if args.browser_path else ""
        scraper.driver = selenium.webdriver.Chrome(options=options)
    elif args.browser == "firefox":
        options = selenium.webdriver.FirefoxOptions()
        if args.headless:
            # If headless_path is set, use the binary at that path
            logger.info("Using Firefox headless")
            options.add_argument("--headless")
        else:
            logger.info("Not using headlessly")
        options.binary_location = args.browser_path if args.browser_path else ""
        scraper.driver = selenium.webdriver.Firefox(options=options)
    elif args.browser == "edge":
        options = selenium.webdriver.EdgeOptions()
        logger.info("Using Edge")
        options.binary_location = args.browser_path if args.browser_path else ""
        scraper.driver = selenium.webdriver.Edge(options=options)
    elif args.browser == "safari":
        logger.info("Using Safari")
        options = selenium.webdriver.SafariOptions()
        # options.binary_location = args.browser_path if args.browser_path else ""
        scraper.driver = selenium.webdriver.Safari(options=options)
    else:
        raise ValueError("Invalid browser")

    for s in config["scrapers"]:
        notifiers = []
        for n in s["notifiers"]:
            # Check if the notify_on values are valid (check against Notifier.NotifyOn)
            notify_on_list = []
            # for notify_on in n["config"]["notify_on"]:
            for notify_on in n["config"].get("notify_on", []):
                if notify_on not in [
                    no.value for no in list(notifier.Notifier.NotifyOn)
                ]:
                    raise ValueError(f"Invalid notify_on value: {notify_on}")
                else:
                    # Get the Enum object from the string value
                    notify_on_list.append(notifier.Notifier.NotifyOn(notify_on))
            if n["type"] == "webhook":
                notifiers.append(
                    notifier.Webhook(
                        url=n["config"]["url"],
                        content_field=n["config"].get("content_field", "content"),
                        notify_on=notify_on_list,
                    )
                )
            elif n["type"] == "ntfy":
                # TODO: Check if optional values are present since right now, a KeyError will be raised if they are not
                notifiers.append(
                    notifier.Ntfy(
                        url=n["config"]["url"],
                        notify_on=notify_on_list,
                        on_click=n["config"].get("on_click", None),
                        priority=n["config"].get("priority", None),
                        tags=n["config"].get("tags", None),
                    )
                )
        UrlScraper(
            url=s["url"],
            css_selector=s["css_selector"],
            interval=s.get("interval", 60),
            verbose_notifications=s.get("verbose_notifications", False),
            notifiers=notifiers,
            # TODO: When the configuration options are improved, configure this via the config file instead
            scroll_to_bottom=s.get("scroll_to_bottom", False),
        )
    UrlScraper.clean_db()
    try:
        while True:
            UrlScraper.scrape_all_urls()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected; exiting")
        scraper.driver.quit()
        exit(0)


if __name__ == "__main__":
    main()
