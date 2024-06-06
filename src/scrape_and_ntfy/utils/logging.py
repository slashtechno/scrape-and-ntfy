from sys import stderr

from loguru import logger

from scrape_and_ntfy.utils.cli_args import args


logging_file = stderr


def set_primary_logger(log_level):
    """Set up the primary logger with the specified log level. Output to stderr and use the format specified."""
    logger.remove()
    # ^10 is a formatting directive to center with a padding of 10
    logger_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> |<level>{level: ^10}</level>| <level>{message}</level>"
    sink = stderr
    logger.add(sink=sink, format=logger_format, colorize=True, level=log_level)


set_primary_logger(args.log_level)
