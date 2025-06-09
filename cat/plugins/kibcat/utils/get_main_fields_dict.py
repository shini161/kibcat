import json
from typing import Any, Type, cast

from kiblog import BaseLogger


def get_main_fields_dict(fields_json_path: str | None, logger: Type[BaseLogger] | None) -> dict[str, Any]:
    """
    Load the main fields dictionary from the JSON file specified by the FIELDS_JSON_PATH environment variable.

    Returns:
        A dictionary parsed from the JSON file, or an empty dict if the path is not set or an error occurs.
    """

    if not fields_json_path:
        msg = "FIELDS_JSON_PATH environment variable is not set."
        if logger:
            logger.error(msg)
        return {}

    try:
        with open(fields_json_path, "r", encoding="utf-8") as file:
            return cast(dict[str, Any], json.load(file))

    except (OSError, json.JSONDecodeError) as e:
        # OSError covers file not found, permission issues, etc.
        # JSONDecodeError covers invalid JSON structure
        msg = f"Error reading or parsing main fields JSON file: {e}"
        if logger:
            logger.error(msg)
        return {}
