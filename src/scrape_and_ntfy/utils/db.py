import dataset
from scrape_and_ntfy.utils.cli_args import args
from scrape_and_ntfy.utils.logging import logger
def connect_to_db(db_url: str):
    global db
    logger.info(f"Connecting to database at {db_url}")
    db = dataset.connect(args.db_url)
    logger.info("Connected to database")

connect_to_db(args.db_url)