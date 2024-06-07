from scrape_and_ntfy.utils.logging import logger
from scrape_and_ntfy.utils.cli_args import args
from scrape_and_ntfy.scraping import scraper, UrlScraper, Webhook
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
            if n["type"] == "webhook":
                notifiers.append(Webhook(url=n["config"]["url"]))
        UrlScraper(url=s["url"], css_selector=s["css_selector"], interval=s["interval"], notifiers=notifiers)
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
