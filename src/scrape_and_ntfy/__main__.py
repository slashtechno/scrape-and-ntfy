from scrape_and_ntfy.utils.logging import logger
from scrape_and_ntfy.utils.cli_args import args
from scrape_and_ntfy.scraping import scraper
import selenium
import dataset

def main():
    logger.debug(f"Args: {args}")
    logger.info("Connecting to DB")
    scraper.db = dataset.connect("sqlite:///db.db")
    scraper.driver = selenium.webdriver.Chrome(args.webdriver_path)
    logger.info("Connected to DB")
    



if __name__ == "__main__":
    main()