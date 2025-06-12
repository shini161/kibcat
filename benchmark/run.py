import argparse
import json
import logging
import os
import shutil
import sys
from typing import Any

from benchmark.cc_bench_utils.exceptions import (
    AuthenticationException,
    GenericRequestException,
)
from benchmark.cc_bench_utils.models import LLMOpenAIChatConfig
from benchmark.cc_bench_utils.rest_api_client import CCApiClient
from benchmark.cc_bench_utils.stopwatch import time_ms


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cheshire Cat API Chat Script")
    parser.add_argument(
        "--config-file",
        type=str,
        default="benchmark/config.json",
        help="Path to config file (default: config.json)",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Set log level (default: info)",
    )
    return parser.parse_args()


def load_config(args: argparse.Namespace, logger: logging.Logger) -> dict[str, Any]:
    config_file = args.config_file
    example_file = os.path.join(os.path.dirname(config_file), "config.example.json")

    # If config file is missing or empty, copy from example
    if not os.path.exists(config_file) or os.path.getsize(config_file) == 0:
        if os.path.exists(example_file):
            shutil.copyfile(example_file, config_file)
            logger.info(
                "'%s' was missing or empty. Copied from '%s'.",
                config_file,
                example_file,
            )
        else:
            logger.error("Config file '%s' not found and no example config present.", config_file)
            sys.exit(1)

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return dict(json.load(f))
    except json.JSONDecodeError as e:
        logger.error("Failed to decode JSON in '%s': %s", config_file, e)
        sys.exit(1)


def load_logger(args: argparse.Namespace) -> logging.Logger:
    # Set up logging
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="%(levelname)s %(message)s")
    return logging.getLogger("benchmark")


def print_average_run_times(results: list[list[dict[str, float]]], logger: logging.Logger) -> None:
    # Calculate averages for each model in each conversation across runs
    num_runs = len(results)
    if num_runs == 0:
        logger.warning("No runs were completed. Cannot calculate averages.")
    else:
        # Check if we have conversations in the results
        if len(results[0]) == 0:
            logger.warning("No conversations were recorded in the runs.")
        else:
            num_conversations = len(results[0])
            logger.info("----- AVERAGE TIMES ACROSS %d RUNS -----", num_runs)

            # Get all unique model names from the first run
            model_names: set[str] = set()
            for conv in results[0]:
                model_names.update(conv.keys())

            # Calculate average for each model in each conversation
            for i in range(num_conversations):
                logger.info("Conversation %d averages:", i + 1)
                for model in model_names:
                    # Sum times for this model in this conversation across all runs
                    total_time = sum(results[run][i][model] for run in range(num_runs))
                    avg_time = total_time / num_runs
                    logger.info("  %s: %.2f ms", model, avg_time)


def execute_run(client: "CCApiClient", logger: logging.Logger, config: dict[str, Any]) -> list[dict[str, float]]:
    # Run results has this structure:
    # [
    #   [ RUN NUMBER 1
    #     {'gpt-4.1-mini': 2259.413499999937, 'gpt-4o-mini': 2576.4378999992914},  CONVERSATION 1
    #     {'gpt-4.1-mini': 5471.280599998863, 'gpt-4o-mini': 5148.826099999496}    CONVERSATION 2
    #   ],
    #   [ RUN NUMBER 2
    #     {'gpt-4.1-mini': 2259.413499999937, 'gpt-4o-mini': 2576.4378999992914},  CONVERSATION 1
    #     {'gpt-4.1-mini': 5471.280599998863, 'gpt-4o-mini': 5148.826099999496}    CONVERSATION 2
    #   ]
    # ]
    run_results = []
    for i, conversation in enumerate(config.get("conversations", [])):
        logger.info("Conversation %s", i + 1)

        conversation_results = {}
        for llm_settings in config.get("llm_config", []):
            llm_settings = LLMOpenAIChatConfig.from_json(llm_settings)
            client.set_llm(llm_settings)
            model_name = llm_settings.model_name

            logger.debug("Using LLM: %s", model_name)

            conversation_results[model_name] = 0.0
            elapsed_time_message = 0.0
            for message in conversation:
                message_text, elapsed_time_message = time_ms(client.send_message, message=message)
                conversation_results[model_name] += elapsed_time_message
                logger.debug("Response (%.2f ms): %s", elapsed_time_message, message_text)
            logger.debug("Total time: %.2f ms", conversation_results[model_name])
            client.clean_memory()
        run_results.append(conversation_results)
    return run_results


def main() -> None:
    args = parse_args()
    logger = load_logger(args)
    config = load_config(args, logger)

    client = CCApiClient(
        base_url=config.get("base_url", "127.0.0.1"),
        port=int(config.get("port", 1865)),
        user_id=config.get("user_id", "testing_user"),
        timeout=int(config.get("timeout", 60)),
    )
    client.connect(
        username=config.get("username", "admin"),
        password=config.get("password", "admin"),
    )
    try:
        client.clean_memory()
    except AuthenticationException as e:
        logger.error("Connection error: %s", e)
    except ValueError as e:
        logger.error("Value error: %s", e)
    except GenericRequestException as e:
        logger.error("An unexpected error occurred: %s", e)

    results = []
    for i in range(config.get("num_runs", 1)):
        logger.info("----- RUN #%i -----", i + 1)
        results.append(execute_run(client, logger, config))
    client.close()

    logger.debug(results)

    print_average_run_times(results, logger)


if __name__ == "__main__":
    main()
