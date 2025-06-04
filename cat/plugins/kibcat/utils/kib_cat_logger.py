from cat.log import log
from cat.plugins.kibcat.imports.kiblog import BaseLogger


class KibCatLogger(BaseLogger):
    """Wrapper of the class BaseLogger to log using the cat's logger"""

    @staticmethod
    def message(message: str):
        log.info(message)

    @staticmethod
    def warning(message: str):
        log.warning(message)

    @staticmethod
    def error(message: str):
        log.error(message)
