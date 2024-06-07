from scrape_and_ntfy.utils.logging import logger
from scrape_and_ntfy.utils.cli_args import args
from scrape_and_ntfy.scraping import scraper, UrlScraper
import selenium
import dataset


def main():
    logger.debug(f"Args: {args}")
    logger.info("Connecting to DB")
    scraper.db = dataset.connect(args.db_url)
    logger.info("Connected to DB")
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
    UrlScraper(
        url="https://www.example.com",
        css_selector="h1",
        interval=5,
    )
    UrlScraper.clean_db()
    while True:
        UrlScraper.scrape_all_urls()

if __name__ == "__main__":
    main()
