from typing import Any

import tiktoken
from cat.convo.messages import CatMessage
from cat.log import log
from cat.mad_hatter.decorators import hook, tool
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult


class TokenCounterHandler(BaseCallbackHandler):
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.input_tokens = 0
        self.output_tokens = 0
        try:
            # Attempt to get the encoding for the specified model
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # Fallback to a default encoding if the model is not recognized
            log.warning(f"Model {model_name} not recognized by tiktoken, using default encoding.")
            # Use a default encoding, e.g., 'cl100k_base'
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def _count_tokens(self, text: str) -> int:
        """Count the number of tokens in a given text."""
        return len(self.encoding.encode(text))

    def on_llm_start(
        self, serialized: dict[str, Any], prompts: list[str], **kwargs: Any
    ) -> None:
        # Get corresponding encoding for the model
        self.input_tokens += self._count_tokens(prompts[0])

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        # Get corresponding encoding for the model
        self.output_tokens += self._count_tokens(response.generations[0][0].text)


def add_callback_if_not_exists(cat: Any) -> None:
    """
    Add a callback to the cat's LLM if it doesn't already exist.
    """
    if cat._llm.callbacks is None:
        callback_token_counter = TokenCounterHandler(model_name=cat._llm.model_name)
        cat._llm.callbacks = [callback_token_counter]
        log.info("Token counting handler initialized.")


@hook
def after_cat_bootstrap(cat):
    add_callback_if_not_exists(cat)


@hook  # default priority = 1
def before_cat_reads_message(user_message_json, cat):
    """
    This hook is called before the cat reads a user message.
    It ensures that the token counting handler is added to the cat's LLM.
    Necessary for the model is updated without restarting the cat (no hook for that).
    """
    add_callback_if_not_exists(cat)
    return user_message_json


@hook
def agent_fast_reply(fast_reply, cat):

    history = cat.working_memory.history
    if not any([isinstance(element, CatMessage) for element in history]):
        # If the user has reset the conversation then reset the token count
        cat._llm.callbacks[0].input_tokens = 0
        cat._llm.callbacks[0].output_tokens = 0

    return fast_reply


@tool(return_direct=True)
def get_token_count(tool_input, cat):
    """
    Get the total number of output tokens used by the LLM. Input is always None.
    """
    try:
        return (
            f"Input tokens: {cat._llm.callbacks[0].input_tokens}\n"
            f"Output tokens: {cat._llm.callbacks[0].output_tokens}"
        )
    except Exception as e:
        return f"Error retrieving token count: {e}"
