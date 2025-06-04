class BaseLogger:
    """
    Base logger class for all functions in this repo.
    Will be wrapped by another class to use the cat's logger once in the plugin
    """

    @staticmethod
    def message(message: str) -> None:
        print(message)

    @staticmethod
    def warning(message: str) -> None:
        print(f"WARNING: {message}")

    @staticmethod
    def error(message: str) -> None:
        print(f"ERROR: {message}")
