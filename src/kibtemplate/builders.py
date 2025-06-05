"""Builders module for rendering Kibana URL templates."""

import inspect
import json
import os
from typing import Any, Type, cast

from jinja2 import Template

from kiblog import BaseLogger
from kibtypes import ParsedKibanaURL

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_FILE_PATH = os.path.join(BASE_DIR, "templates")


def generic_template_renderer(
    templates_path: str,
    template_name: str,
    logger: Type[BaseLogger] | None = None,
    **kwargs: Any,
) -> str:
    """
    Renders a Jinja2 template with given arguments.

    Args:
        templates_path (str): Path to the templates directory.
        template_name (str): Filename of the Jinja2 template.
        logger (Type[BaseLogger] | None): Optional logger.
        **kwargs: Variables passed to the template.

    Returns:
        str: Rendered template as a string.
    """

    msg = f"[kibtemplate.generic_template_renderer] - Rendering {template_name}"
    if logger:
        logger.message(msg)

    template_file_path: str = os.path.join(templates_path, template_name)
    template_str: str | None = None

    try:
        with open(template_file_path, encoding="utf-8") as file:
            template_str = file.read()
    except Exception as e:
        msg = (
            f"[kibtemplate.generic_template_renderer] - Rendering {template_name} - Failed to read template file.\n{e}"
        )
        if logger:
            logger.error(msg)
        raise IOError(msg) from e

    try:
        template = Template(template_str)
    except Exception as e:
        msg = (
            f"[kibtemplate.generic_template_renderer] - Rendering {template_name} - "
            "Failed to compile Jinja2 template.\n{e}"
        )
        if logger:
            logger.error(msg)
        raise RuntimeError(msg) from e

    if logger:
        msg = (
            f"[kibtemplate.generic_template_renderer] - Rendering {template_name} - "
            "Template loaded and compiled successfully."
        )
        logger.message(msg)

    try:
        output_str = template.render(**kwargs)
    except Exception as e:
        msg = f"[kibtemplate.generic_template_renderer] - Rendering {template_name} - Failed to render template.\n{e}"
        if logger:
            logger.error(msg)
        raise RuntimeError(msg) from e

    msg = f"[kibtemplate.generic_template_renderer] - Rendering {template_name} - Template rendered successfully"
    if logger:
        logger.message(msg)

    return cast(str, output_str)


# pylint: disable=too-many-positional-arguments
def build_template(
    base_url: str,
    start_time: str,
    end_time: str,
    visible_fields: list[str],
    filters: list[tuple[str, str]],
    data_view_id: str,
    search_query: str,
    logger: Type[BaseLogger] | None = None,
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
        logger (Type[BaseLogger] | None): Optional logger instance for messaging.

    Returns:
        ParsedKibanaURL: Parsed Kibana URL data loaded from rendered JSON.
    """

    msg = "[kibtemplate.build_template] - Loading template for Kibana URL"
    if logger:
        logger.message(msg)

    output_str = generic_template_renderer(
        templates_path=TEMPLATES_FILE_PATH,
        template_name="url.json.jinja2",
        logger=logger,
        base_url=base_url,
        start_time=start_time,
        end_time=end_time,
        visible_fields=visible_fields,
        filters=filters,
        data_view_id=data_view_id,
        search_query=search_query,
    )

    msg = "[kibtemplate.build_template] - Kibana URL template rendered successfully"
    if logger:
        logger.message(msg)

    try:
        result: ParsedKibanaURL = json.loads(output_str)
    except json.JSONDecodeError as e:
        msg = f"[kibtemplate.build_template] - Rendered template is not valid JSON.\n{e}"
        if logger:
            logger.error(msg)

        current_frame = inspect.currentframe()
        raise json.JSONDecodeError(msg, "builders.py", current_frame.f_lineno if current_frame else 0)

    return result
