import argparse
import json
import logging
import os
import shutil
import sys

from benchmark.cc_bench_utils import AuthenticationException, CCApiClient, GenericRequestException, LLMOpenAIChatConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Cheshire Cat API Chat Script")
    parser.add_argument(
        "--config-file", type=str, default="benchmark/config.json", help="Path to config file (default: config.json)"
    )
    parser.add_argument(
        "-l",
        "--log-level",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Set log level (default: info)",
    )
    args = parser.parse_args()

    # Set up logging
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="%(levelname)s %(message)s")
    logger = logging.getLogger("benchmark")

    config_file = args.config_file
    example_file = os.path.join(os.path.dirname(config_file), "config.example.json")

    # If config file is missing or empty, copy from example
    if not os.path.exists(config_file) or os.path.getsize(config_file) == 0:
        if os.path.exists(example_file):
            shutil.copyfile(example_file, config_file)
            logger.info("'%s' was missing or empty. Copied from '%s'.", config_file, example_file)
        else:
            logger.error("Config file '%s' not found and no example config present.", config_file)
            sys.exit(1)

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        logger.error("Failed to decode JSON in '%s': %s", config_file, e)
        sys.exit(1)

    client = CCApiClient(
        base_url=config.get("base_url", "127.0.0.1"),
        port=int(config.get("port", 1865)),
        user_id=config.get("user_id", "testing_user"),
        timeout=int(config.get("timeout", 60)),
    )
    client.connect(username=config.get("username", "admin"), password=config.get("password", "admin"))
    try:
        client.clean_memory()
    except AuthenticationException as e:
        logger.error("Connection error: %s", e)
    except ValueError as e:
        logger.error("Value error: %s", e)
    except GenericRequestException as e:
        logger.error("An unexpected error occurred: %s", e)

    for i, conversation in enumerate(config.get("conversations", [])):
        logger.info("Conversation %s:", i + 1)
        for llm_settings in config.get("llm_config", []):
            llm_settings = LLMOpenAIChatConfig.from_json(llm_settings)
            client.set_llm(llm_settings)
            logger.info("Using LLM: %s", llm_settings.model_name)
            for message in conversation:
                message_text = client.send_message(message=message)
                logger.debug("Response: %s", message_text)
            client.clean_memory()
    client.close()


if __name__ == "__main__":
    main()
