from typing import Optional, Type
from cat.plugins.kibcat.imports.logging.base_logger import BaseKibCatLogger
from cat.plugins.kibcat.imports.json_template.builders import generic_template_renderer
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_FILE_PATH = os.path.join(BASE_DIR, "templates")


def build_refine_filter_json(
    json_input: str,
    LOGGER: Optional[Type[BaseKibCatLogger]] = None,
) -> str:
    """
    Renders a the refine_filter_json using the given parameter.

    Args:
        json_input (str): The JSON input for the prompt.
        LOGGER (Optional[Type[BaseKibCatLogger]]): Optional logger instance for messaging.

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


def build_agent_prefix(LOGGER: Optional[Type[BaseKibCatLogger]] = None) -> str:
    """
    Returns the LLM prefix from the template.

    Args:
        LOGGER (Optional[Type[BaseKibCatLogger]]): Optional logger instance for messaging.

    Returns:
        str: The LLM prefix.
    """

    result: str = generic_template_renderer(
        templates_path=TEMPLATES_FILE_PATH,
        template_name="cat_prefix.jinja2",
        LOGGER=LOGGER,
    )

    return result


def build_form_data_extractor(
    conversation_history: str,
    LOGGER: Optional[Type[BaseKibCatLogger]] = None,
) -> str:
    """
    Returns the form data extractor from the template.

    Args:
        conversation_history (str): The conversation history loaded as string
        LOGGER (Optional[Type[BaseKibCatLogger]]): Optional logger instance for messaging.

    Returns:
        str: The form data extractor.
    """

    result: str = generic_template_renderer(
        templates_path=TEMPLATES_FILE_PATH,
        template_name="form_data_extractor.jinja2",
        LOGGER=LOGGER,
        conversation_history=conversation_history,
    )

    return result
