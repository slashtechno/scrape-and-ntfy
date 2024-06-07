import argparse
import os
import sys
from pathlib import Path

# Can't do from pystodon.utils import logger since that would cause a circular import
from scrape_and_ntfy.utils.logging import logger

import dotenv


def set_argparse() -> None:
    """
    Set up the argument parser and parse the arguments to args
    """
    global args

    if Path(".env").is_file():
        dotenv.load_dotenv()
        logger.info("Loaded .env file")
    else:
        logger.warning(".env file not found")
    argparser = argparse.ArgumentParser(
        description="Scrape a website and notify regarding specific changes"
    )
    argparser.add_argument(
        "--db-url",
        help="The URL to the database",
        default=os.getenv("DB_URL") if os.getenv("DB_URL") else "sqlite:///db.db",
    )
    argparser.add_argument(
        "--browser",
        help="The browser to use",
        default=os.getenv("BROWSER") if os.getenv("BROWSER") else "chrome",
        choices=["chrome", "firefox", "edge", "safari"],
    )
    debug = argparser.add_argument_group("Debugging options")
    debug.add_argument(
        "--log-level",
        help="The log level to use.",
        default=os.getenv("LOG_LEVEL") if os.getenv("LOG_LEVEL") else "INFO",
    )
    args = argparser.parse_args()


def check_required_args(required_args: list[str], argparser: argparse.ArgumentParser):
    """
    Check if required arguments are set
    Useful if using enviroment variables with argparse as default and required are mutually exclusive
    """
    for arg in required_args:
        args = argparser.parse_args()
        if getattr(args, arg) is None:
            # raise ValueError(f"{arg} is required")
            logger.critical(f"{arg} is required")
            sys.exit(1)


set_argparse()
