"""Base logging class used across KibCat modules."""


class BaseLogger:
    """
    Base logger class for all functions in this repository.

    This class is intended to be subclassed or wrapped by a custom logger
    (e.g. integrating with Cheshire Cat or other systems).
    """

    @staticmethod
    def message(message: str) -> None:
        """
        Log a general informational message.

        Args:
            message (str): The message to log.
        """
        print(message)

    @staticmethod
    def warning(message: str) -> None:
        """
        Log a warning message.

        Args:
            message (str): The warning message to log.
        """
        print(f"WARNING: {message}")

    @staticmethod
    def error(message: str) -> None:
        """
        Log an error message.

        Args:
            message (str): The error message to log.
        """
        print(f"ERROR: {message}")
