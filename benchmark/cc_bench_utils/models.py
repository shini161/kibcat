import dataclasses
from typing import Any, Optional, TypeAlias


@dataclasses.dataclass
class ConversationResult:
    time: float
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


ConversationResults: TypeAlias = dict[str, ConversationResult]
RunResults: TypeAlias = list[ConversationResults]


@dataclasses.dataclass
class LLMOpenAIChatConfig:
    """
    Configuration class for CC LLMs settings.

    This class represents the configuration for LLMs in CC,
    including API key, model name, temperature, streaming settings,
    and token cost information.
    """

    openai_api_key: str = ""
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.7
    streaming: bool = True
    cost_per_million_tokens: dict[str, float] = dataclasses.field(default_factory=lambda: {"input": 0.0, "output": 0.0})

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
                cost_per_million_tokens=config.get("cost_per_million_tokens", {"input": 0.0, "output": 0.0}),
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
            # cost_per_million_tokens is not included in the dict (not required in CC server, only in out benchmark)
        }
