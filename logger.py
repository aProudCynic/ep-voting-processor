import logging
from sys import stdout


def create_logger():
    logging.basicConfig(filename='logger.log', encoding='utf-8', level=logging.DEBUG)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(stdout)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger
