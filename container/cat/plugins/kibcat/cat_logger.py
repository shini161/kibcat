from cat.log import log
from cat.plugins.kibcat.utils.base_logger import BaseKibCatLogger


class KibCatLogger(BaseKibCatLogger):

    @staticmethod
    def message(message: str):
        log.info(message)

    @staticmethod
    def warning(message: str):
        log.warning(message)

    @staticmethod
    def error(message: str):
        log.error(message)
