from scrape_and_ntfy.utils.logging import logger
from scrape_and_ntfy.utils.cli_args import args
from scrape_and_ntfy.scraping import scraper, UrlScraper, Webhook, Notifier
import selenium


def main():
    logger.debug(f"Args: {args}")
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
    if args.webhook_url:
        webhook = Webhook(url=args.webhook_url)
        logger.info(f"Using webhook {webhook.url}")
    else:
        webhook = None
    UrlScraper(
        url="https://www.example.com",
        css_selector="h1",
        interval=5,
        notifiers=[webhook],
    )
    UrlScraper.clean_db()
    Notifier.clean_db()
    try:
        while True:
            UrlScraper.scrape_all_urls()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected; exiting")
        scraper.driver.quit()
        exit(0)

if __name__ == "__main__":
    main()
