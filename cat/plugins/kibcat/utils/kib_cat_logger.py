from cat.log import log
from cat.plugins.kibcat.imports.logging.base_logger import BaseKibCatLogger


class KibCatLogger(BaseKibCatLogger):
    """Wrapper of the class BaseKibCatLogger to log using the cat's logger"""

    @staticmethod
    def message(message: str):
        log.info(message)

    @staticmethod
    def warning(message: str):
        log.warning(message)

    @staticmethod
    def error(message: str):
        log.error(message)
