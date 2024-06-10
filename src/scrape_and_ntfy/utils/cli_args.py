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
        "--db-url",
        help="The URL to the database",
        default=os.getenv("DB_URL")
        if os.getenv("DB_URL")
        else "sqlite:///database/db.db",
    )
    argparser.add_argument(
        "--browser",
        help="The browser to use. Generally, if the browser is based on Chromium, use Chrome and if it's based on Firefox, use Firefox.",
        default=os.getenv("BROWSER") if os.getenv("BROWSER") else "chrome",
        choices=["chrome", "firefox", "edge", "safari"],
    )
    argparser.add_argument(
        "--path-to-toml",
        help="The path to the TOML file",
        default=os.getenv("PATH_TO_TOML")
        if os.getenv("PATH_TO_TOML")
        else "config.toml",
    )
    argparser.add_argument(
        "--headless-path",
        help="The path to whatever browser binary to use headlessly. Ensure this matches --browser/$BROWSER. This does not work with Safari nor Edge.",
        default=os.getenv("HEADLESS_PATH") if os.getenv("HEADLESS_PATH") else "",
        # Not using validate_path_to_file because having "" as the default raises an error
        type=str,
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
    for arg in required_args:
        args = argparser.parse_args()
        if getattr(args, arg) is None:
            # raise ValueError(f"{arg} is required")
            logger.critical(f"{arg} is required")
            sys.exit(1)


set_argparse()
