import argparse
import os
import sys
from pathlib import Path

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
        "--path-to-toml",
        help="The path to the TOML file",
        default=os.getenv("PATH_TO_TOML")
        if os.getenv("PATH_TO_TOML")
        else "config.toml",
    )
    database = argparser.add_argument_group("Database options")
    database.add_argument(
        "--db-url",
        help="The URL to the database",
        default=os.getenv("DB_URL")
        if os.getenv("DB_URL")
        else "sqlite:///database/db.db",
    )
    database.add_argument(
        "--no-clean-db",
        help="Do not clean the database before scraping. Cleaning the database removes entries no longer present in config.toml",
        action="store_true",
        default=True
        if (
            os.getenv("NO_CLEAN_DB")
            and os.getenv("NO_CLEAN_DB").lower() == "true"
            and os.getenv("NO_CLEAN_DB").lower() != "false"
        )
        else False,
    )

    scraping = argparser.add_argument_group("Scraping options")
    scraping.add_argument(
        "--scroll-to-bottom",
        help="Attempt to scroll to the bottom of the page before scraping. Read https://stackoverflow.com/a/27760083 for more information",
        action="store_true",
        default=True
        if (
            os.getenv("SCROLL_TO_BOTTOM")
            and os.getenv("SCROLL_TO_BOTTOM").lower() == "true"
            and os.getenv("SCROLL_TO_BOTTOM").lower() != "false"
        )
        else False,
    )
    scraping.add_argument(
        "--browser",
        help="The browser to use. Generally, if the browser is based on Chromium, use Chrome and if it's based on Firefox, use Firefox.",
        default=os.getenv("BROWSER") if os.getenv("BROWSER") else "chrome",
        choices=["chrome", "firefox", "edge", "safari"],
    )
    scraping.add_argument(
        "--browser-path",
        help="The path to the browser binary",
        default=os.getenv("BROWSER_PATH") if os.getenv("BROWSER_PATH") else "",
        # type=validate_path_to_file,
        type=str,
    )
    scraping.add_argument(
        "--headless",
        help="Use headless mode",
        action="store_true",
        default=True
        if (
            os.getenv("HEADLESS")
            and os.getenv("HEADLESS").lower() == "true"
            and os.getenv("HEADLESS").lower() != "false"
        )
        else False,
    )
    debug = argparser.add_argument_group("Debugging options")
    debug.add_argument(
        "--log-level",
        help="The log level to use.",
        default=os.getenv("LOG_LEVEL") if os.getenv("LOG_LEVEL") else "INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    args = argparser.parse_args()


# def validate_path_to_file(path: str) -> str:
#     """
#     Validate that the path to the file exists
#     """
#     if Path(path).is_file():
#         return path
#     else:
#         raise argparse.ArgumentTypeError(f"File {path} is not a file (or does not exist)")


def check_required_args(required_args: list[str], argparser: argparse.ArgumentParser):
    """
    Check if required arguments are set
    Useful if using enviroment variables with argparse as default and required are mutually exclusive
    """
    args = argparser.parse_args()
    for arg in required_args:
        if getattr(args, arg) is None:
            # raise ValueError(f"{arg} is required")
            logger.critical(f"{arg} is required")
            sys.exit(1)


set_argparse()
