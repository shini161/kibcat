import os
from typing import Optional, Type

from kiblog import BaseLogger
from kibtemplate.builders import generic_template_renderer

from ..defaults import DEFAULT_END_TIME, DEFAULT_START_TIME

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_FILE_PATH = os.path.join(BASE_DIR, "templates")


def build_refine_filter_json(
    json_input: str,
    operators_str: str,
    logger: Optional[Type[BaseLogger]] = None,
) -> str:
    """
    Renders a the refine_filter_json using the given parameter.

    Args:
        json_input (str): The JSON input for the prompt.
        operators_str (str): The list of operators from the ENUM as JSON loaded as string.
        logger (Optional[Type[BaseLogger]]): Optional logger instance for messaging.

    Returns:
        str: The rendered prompt with the given input JSON.
    """

    result: str = generic_template_renderer(
        templates_path=TEMPLATES_FILE_PATH,
        template_name="refine_filter_json_prompt.jinja2",
        logger=logger,
        operators_str=operators_str,
        json_input=json_input,
    )

    return result


def build_agent_prefix(logger: Optional[Type[BaseLogger]] = None) -> str:
    """
    Returns the LLM prefix from the template.

    Args:
        logger (Optional[Type[BaseLogger]]): Optional logger instance for messaging.

    Returns:
        str: The LLM prefix.
    """

    result: str = generic_template_renderer(
        templates_path=TEMPLATES_FILE_PATH,
        template_name="cat_prefix.jinja2",
        logger=logger,
    )

    return result


def build_form_data_extractor(
    conversation_history: str,
    main_fields_str: str,
    operators_str: str,
    logger: Optional[Type[BaseLogger]] = None,
) -> str:
    """
    Returns the form data extractor from the template.

    Args:
        conversation_history (str): The conversation history loaded as string
        main_fields_str (str): The main fields JSON loaded as string
        operators_str (str): The list of operators from the ENUM as JSON loaded as string
        logger (Optional[Type[BaseLogger]]): Optional logger instance for messaging.

    Returns:
        str: The form data extractor.
    """

    result: str = generic_template_renderer(
        templates_path=TEMPLATES_FILE_PATH,
        template_name="form_data_extractor.jinja2",
        logger=logger,
        conversation_history=conversation_history,
        main_fields_str=main_fields_str,
        operators_str=operators_str,
    )

    return result


def build_form_confirm_message(
    conversation_history: str,
    applied_filters: str,
    query: str,
    logger: Optional[Type[BaseLogger]] = None,
) -> str:
    """
    Returns the form confirm message from the template.

    Args:
        conversation_history (str): The conversation history loaded as string
        main_fields_str (str): The main fields JSON loaded as string
        query (str): The query string to be confirmed.
        logger (Optional[Type[BaseLogger]]): Optional logger instance for messaging.

    Returns:
        str: The form confirm message.
    """

    result: str = generic_template_renderer(
        templates_path=TEMPLATES_FILE_PATH,
        template_name="form_confirm_message.jinja2",
        logger=logger,
        conversation_history=conversation_history,
        applied_filters=applied_filters,
        query=query,
        DEFAULT_START_TIME=DEFAULT_START_TIME,
        DEFAULT_END_TIME=DEFAULT_END_TIME,
    )

    return result


def build_form_check_exit_intent(
    last_message: str,
    logger: Optional[Type[BaseLogger]] = None,
) -> str:
    """
    Returns the prompt used to check if the user wants to exit the form.

    Args:
        last_message (str): The last message from the conversation history.
        logger (Optional[Type[BaseLogger]]): Optional logger instance for messaging.

    Returns:
        str: The form print message.
    """

    result: str = generic_template_renderer(
        templates_path=TEMPLATES_FILE_PATH,
        template_name="form_check_exit_intent.jinja2",
        logger=logger,
        last_message=last_message,
    )

    return result


def build_form_end_message(
    conversation_history: str,
    logger: Optional[Type[BaseLogger]] = None,
) -> str:
    """
    Returns the form end message from the template.

    Args:
        conversation_history (str): The conversation history loaded as string
        main_fields_str (str): The main fields JSON loaded as string
        logger (Optional[Type[BaseLogger]]): Optional logger instance for messaging.

    Returns:
        str: The form end message.
    """

    result: str = generic_template_renderer(
        templates_path=TEMPLATES_FILE_PATH,
        template_name="form_end_message.jinja2",
        logger=logger,
        conversation_history=conversation_history,
    )

    return result
