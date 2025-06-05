import inspect
import json
import os
from typing import Any, Type, cast

from jinja2 import Template

from kiblog import BaseLogger
from kibtypes import ParsedKibanaURL

from .kibcat_filter import FilterOperators, KibCatFilter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_FILE_PATH = os.path.join(BASE_DIR, "templates")

TEMPLATE_MAIN_NAME = "url.json.jinja2"
FILTER_IS_TEMPLATE_NAME = "filter_is.json.jinja2"
FILTER_IS_ONE_OF_TEMPLATE_NAME = "filter_is_one_of.json.jinja2"
FILTER_EXISTS_NAME = "filter_exists.json.jinja2"


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
    filters: list[KibCatFilter],
    data_view_id: str,
    search_query: str,
    refresh_interval: int = 60000,
    is_refresh_paused: bool = True,
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
    if logger:
        msg = "[kibtemplate.build_template] - Generating filters from templates"
        logger.message(msg)

    rendered_filters: list[str] = []

    for filter in filters:
        filter_operator: FilterOperators = filter.operator
        filter_field: str = filter.field
        filter_value: str | list[str] = filter.value

        template_name: str
        template_args: dict[str, Any] = {}

        template_args["field_name"] = filter_field
        template_args["data_view_id"] = data_view_id

        match filter_operator:
            case FilterOperators.IS | FilterOperators.IS_NOT:
                template_name = "filter_is.json.jinja2"

                template_args["negate"] = filter_operator is FilterOperators.IS_NOT
                template_args["expected_value"] = filter_value

            case FilterOperators.IS_ONE_OF | FilterOperators.IS_NOT_ONE_OF:
                template_name = "filter_is_one_of.json.jinja2"

                template_args["negate"] = filter_operator is FilterOperators.IS_NOT_ONE_OF
                template_args["expected_values"] = filter_value

            case FilterOperators.EXISTS | FilterOperators.NOT_EXISTS:
                template_name = "filter_exists.json.jinja2"

                template_args["negate"] = filter_operator is FilterOperators.NOT_EXISTS

            case _:
                continue

        rendered_filter = generic_template_renderer(
            templates_path=TEMPLATES_FILE_PATH, template_name=template_name, logger=logger, **template_args
        )
        rendered_filters.append(rendered_filter)

    if logger:
        msg = "[kibtemplate.build_template] - Loading template for Kibana URL"
        logger.message(msg)

    # pylint: disable=duplicate-code
    output_str = generic_template_renderer(
        templates_path=TEMPLATES_FILE_PATH,
        template_name=TEMPLATE_MAIN_NAME,
        logger=logger,
        base_url=base_url,
        start_time=start_time,
        end_time=end_time,
        refresh_paused=is_refresh_paused,
        refresh_interval=refresh_interval,
        visible_fields=visible_fields,
        filters=rendered_filters,
        data_view_id=data_view_id,
        search_query=search_query,
    )

    if logger:
        msg = "[kibtemplate.build_template] - Kibana URL template rendered successfully"
        logger.message(msg)

    try:
        result: ParsedKibanaURL = json.loads(output_str)
    except json.JSONDecodeError as e:
        if logger:
            msg = f"[kibtemplate.build_template] - Rendered template is not valid JSON.\n{e}"
            logger.error(msg)

        current_frame = inspect.currentframe()
        raise json.JSONDecodeError(msg, "builders.py", current_frame.f_lineno if current_frame else 0)

    return result
