from typing import Any


class LLMOpenAIChatConfig:
    """
    Configuration class for OpenAI Chat LLM settings.

    This class represents the configuration for OpenAI Chat LLM,
    including API key, model name, temperature, and streaming settings.
    """

    def __init__(
        self,
        openai_api_key: str,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.7,
        streaming: bool = True,
    ):
        """
        Initialize OpenAI Chat LLM configuration.

        Args:
        openai_api_key (str): OpenAI API key
        model_name (str): Name of the OpenAI model to use
        temperature (float): Temperature setting for generation
        streaming (bool): Whether to use streaming mode
        """
        self.openai_api_key = openai_api_key
        self.model_name = model_name
        self.temperature = temperature
        self.streaming = streaming

    @classmethod
    def from_json(cls, json_data: dict[str, Any]) -> "LLMOpenAIChatConfig":
        """
        Create an instance from JSON data.

        Args:
        json_data (dict[str, Any]): JSON data containing configuration

        Returns:
        LLMOpenAIChatConfig: New instance with the provided configuration
        """
        if isinstance(json_data, dict):
            if "value" in json_data and isinstance(json_data["value"], dict):
                # If the JSON follows the {"name": X, "value": {settings}} format
                config = json_data["value"]
            else:
                # If the JSON is just the settings dict
                config = json_data

            return cls(
                openai_api_key=config.get("openai_api_key", ""),
                model_name=config.get("model_name", "gpt-4o-mini"),
                temperature=config.get("temperature", 0.7),
                streaming=config.get("streaming", True),
            )
        raise ValueError("Invalid JSON data format")

    def to_dict(self) -> dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
        dict[str, Any]: dictionary representation of the configuration
        """
        return {
            "name": "LLMOpenAIChatConfig",
            "openai_api_key": self.openai_api_key,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "streaming": self.streaming,
        }
