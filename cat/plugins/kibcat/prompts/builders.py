import os
from typing import Optional, Type

from cat.plugins.kibcat.imports.kiblog import BaseLogger
from cat.plugins.kibcat.imports.kibtemplate.builders import generic_template_renderer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_FILE_PATH = os.path.join(BASE_DIR, "templates")


def build_refine_filter_json(
    json_input: str,
    LOGGER: Optional[Type[BaseLogger]] = None,
) -> str:
    """
    Renders a the refine_filter_json using the given parameter.

    Args:
        json_input (str): The JSON input for the prompt.
        LOGGER (Optional[Type[BaseLogger]]): Optional logger instance for messaging.

    Returns:
        str: The rendered prompt with the given input JSON.
    """

    result: str = generic_template_renderer(
        templates_path=TEMPLATES_FILE_PATH,
        template_name="refine_filter_json_prompt.jinja2",
        LOGGER=LOGGER,
        json_input=json_input,
    )

    return result


def build_agent_prefix(LOGGER: Optional[Type[BaseLogger]] = None) -> str:
    """
    Returns the LLM prefix from the template.

    Args:
        LOGGER (Optional[Type[BaseLogger]]): Optional logger instance for messaging.

    Returns:
        str: The LLM prefix.
    """

    result: str = generic_template_renderer(
        templates_path=TEMPLATES_FILE_PATH,
        template_name="cat_prefix.jinja2",
        LOGGER=LOGGER,
    )

    return result


def build_add_filter_tool_prefix(
    main_fields_str: str,
    LOGGER: Optional[Type[BaseLogger]] = None,
) -> str:
    """
    Returns the add_filter tool's from the template.

    Args:
        main_fields_str (str): The main fields JSON loaded as string
        LOGGER (Optional[Type[BaseLogger]]): Optional logger instance for messaging.

    Returns:
        str: The add_filter tool's prefix.
    """

    result: str = generic_template_renderer(
        templates_path=TEMPLATES_FILE_PATH,
        template_name="add_filter_tool_prefix.jinja2",
        LOGGER=LOGGER,
        main_fields_str=main_fields_str,
    )

    return result
