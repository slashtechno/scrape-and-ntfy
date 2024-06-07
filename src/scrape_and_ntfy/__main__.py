from scrape_and_ntfy.utils.logging import logger
from scrape_and_ntfy.utils.cli_args import args
from scrape_and_ntfy.scraping import scraper, UrlScraper
from scrape_and_ntfy.scraping import notifier
import selenium
import toml


def main():
    logger.debug(f"Args: {args}")
    config = toml.load(args.path_to_toml)
    match args.browser:
        case "chrome":
            logger.info("Using Chrome")
            scraper.driver = selenium.webdriver.Chrome()
        case "firefox":
            logger.info("Using Firefox")
            scraper.driver = selenium.webdriver.Firefox()
        case "edge":
            logger.info("Using Edge")
            scraper.driver = selenium.webdriver.Edge()
        case "safari":
            logger.info("Using Safari")
            scraper.driver = selenium.webdriver.Safari()

    for s in config["scrapers"]:
        notifiers = []
        for n in s["notifiers"]:
            # Check if the notify_on values are valid (check against Notifier.NotifyOn)
            notify_on_list = []
            for notify_on in n["config"]["notify_on"]:
                if notify_on not in [no.value for no in list(notifier.Notifier.NotifyOn)]:
                    raise ValueError(f"Invalid notify_on value: {notify_on}")
                else:
                    # Get the Enum object from the string value
                    notify_on_list.append(notifier.Notifier.NotifyOn(notify_on))
            if n["type"] == "webhook":
                notifiers.append(notifier.Webhook(url=n["config"]["url"], notify_on=notify_on_list))
            elif n["type"] == "ntfy":
                notifiers.append(notifier.Ntfy(url=n["config"]["url"], notify_on=notify_on_list, on_click=n["config"]["on_click"], priority=n["config"]["priority"], tags=n["config"]["tags"]))
        UrlScraper(
            url=s["url"],
            css_selector=s["css_selector"],
            interval=s["interval"],
            notifiers=notifiers,
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
