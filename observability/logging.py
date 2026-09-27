import logging
import sys

logger = logging.getLogger("knowledge-search")
logger.setLevel(logging.INFO)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    handler.setFormatter(formatter)

    logger.addHandler(handler)

    logger.propagate = False
