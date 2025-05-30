from jinja2 import Template
from typing import Any, Optional, Type
from ..logging.base_logger import BaseKibCatLogger
from ..kibcat_types.parsed_kibana_url import ParsedKibanaURL
import os
import json
import inspect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_FILE_PATH = os.path.join(BASE_DIR, "templates")


def generic_template_renderer(
    templates_path: str,
    template_name: str,
    LOGGER: Optional[Type[BaseKibCatLogger]] = None,
    **kwargs: Any,
) -> str:

    if LOGGER:
        LOGGER.message(f"generic_template_renderer - Rendering {template_name}")

    template_file_path: str = os.path.join(templates_path, template_name)
    template_str: Optional[str] = None

    try:
        with open(template_file_path) as file:
            template_str = file.read()
    except Exception as e:
        msg = f"generic_template_renderer - Rendering {template_name} - Failed to read template file.\n{e}"
        if LOGGER:
            LOGGER.error(msg)
        raise IOError(msg)

    try:
        template = Template(template_str)
    except Exception as e:
        msg = f"generic_template_renderer - Rendering {template_name} - Failed to compile Jinja2 template.\n{e}"
        if LOGGER:
            LOGGER.error(msg)
        raise Exception(msg)

    if LOGGER:
        msg = f"generic_template_renderer - Rendering {template_name} - Template loaded and compiled successfully."
        LOGGER.message(msg)

    try:
        output_str = template.render(**kwargs)
    except Exception as e:
        msg = f"generic_template_renderer - Rendering {template_name} - Failed to render template.\n{e}"
        if LOGGER:
            LOGGER.error(msg)
        raise Exception(msg)

    if LOGGER:
        LOGGER.message(
            f"generic_template_renderer - Rendering {template_name} - Template rendered successfully"
        )

    return output_str


def build_template(
    base_url: str,
    start_time: str,
    end_time: str,
    visible_fields: list[str],
    filters: list[tuple[str, str]],
    data_view_id: str,
    search_query: str,
    LOGGER: Optional[Type[BaseKibCatLogger]] = None,
) -> ParsedKibanaURL:
    """
    Renders a Kibana URL JSON structure using a Jinja2 template and provided parameters.

    Args:
        base_url (str): The base URL for Kibana.
        start_time (str): The start time for the time filter.
        end_time (str): The end time for the time filter.
        visible_fields (list[str]): List of fields to show in the view.
        filters (list[tuple[str, str]]): List of key-value filter pairs.
        data_view_id (str): The data view ID to be used.
        search_query (str): The search query string.
        LOGGER (Optional[Type[BaseKibCatLogger]]): Optional logger instance for messaging.

    Returns:
        ParsedKibanaURL: Parsed Kibana URL data loaded from rendered JSON.
    """

    if LOGGER:
        LOGGER.message("build_template - Loading template for Kibana URL")

    output_str = generic_template_renderer(
        templates_path=TEMPLATES_FILE_PATH,
        template_name="url.json.jinja2",
        LOGGER=LOGGER,
        base_url=base_url,
        start_time=start_time,
        end_time=end_time,
        visible_fields=visible_fields,
        filters=filters,
        data_view_id=data_view_id,
        search_query=search_query,
    )

    if LOGGER:
        LOGGER.message("build_template - Kibana URL template rendered successfully")

    try:
        result: ParsedKibanaURL = json.loads(output_str)
    except json.JSONDecodeError as e:
        msg = f"build_template - Rendered template is not valid JSON.\n{e}"
        if LOGGER:
            LOGGER.error(msg)

        current_frame = inspect.currentframe()
        raise json.JSONDecodeError(
            msg, "builders.py", current_frame.f_lineno if current_frame else 0
        )

    return result
