class BaseKibCatLogger:
    """
    Base logger class for all functions in this repo.
    Will be wrapped by another class to use the cat's logger once in the plugin
    """

    @staticmethod
    def message(message: str):
        print(message)

    @staticmethod
    def warning(message: str):
        print(f"WARNING: {message}")

    @staticmethod
    def error(message: str):
        print(f"ERROR: {message}")
