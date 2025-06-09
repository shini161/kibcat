from cat.log import log

from kiblog import BaseLogger


class KibCatLogger(BaseLogger):
    """Wrapper of the class BaseLogger to log using the cat's logger"""

    @staticmethod
    def message(message: str) -> None:
        log.info(message)

    @staticmethod
    def warning(message: str) -> None:
        log.warning(message)

    @staticmethod
    def error(message: str) -> None:
        log.error(message)
