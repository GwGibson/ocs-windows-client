import logging


def setup_custom_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Console handler for INFO level
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.INFO)
    c_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    logger.addHandler(c_handler)

    # Console handler for ERROR level
    e_handler = logging.StreamHandler()
    e_handler.setLevel(logging.ERROR)
    e_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    e_handler.setFormatter(e_format)
    logger.addHandler(e_handler)

    return logger
