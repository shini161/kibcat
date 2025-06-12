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
from benchmark.cc_bench_utils.models import LLMOpenAIChatConfig, RunResults
from benchmark.cc_bench_utils.rest_api_client import CCApiClient
from benchmark.cc_bench_utils.stopwatch import time_ms


class BenchmarkRunner:
    def __init__(self) -> None:
        self.args = self.parse_args()
        self.logger = self.load_logger()
        self.config = self.load_config()
        self.client = self.initialize_client()

    def parse_args(self) -> argparse.Namespace:
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

    def load_logger(self) -> logging.Logger:
        # Set up logging
        log_level = getattr(logging, self.args.log_level.upper(), logging.INFO)
        logging.basicConfig(level=log_level, format="%(levelname)s %(message)s")
        return logging.getLogger("benchmark")

    def load_config(self) -> dict[str, Any]:
        config_file = self.args.config_file
        example_file = os.path.join(os.path.dirname(config_file), "config.example.json")

        # If config file is missing or empty, copy from example
        if not os.path.exists(config_file) or os.path.getsize(config_file) == 0:
            if os.path.exists(example_file):
                shutil.copyfile(example_file, config_file)
                self.logger.info(
                    "'%s' was missing or empty. Copied from '%s'.",
                    config_file,
                    example_file,
                )
            else:
                self.logger.error("Config file '%s' not found and no example config present.", config_file)
                sys.exit(1)

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return dict(json.load(f))
        except json.JSONDecodeError as e:
            self.logger.error("Failed to decode JSON in '%s': %s", config_file, e)
            sys.exit(1)

    def initialize_client(self) -> "CCApiClient":
        return CCApiClient(
            base_url=self.config.get("base_url", "127.0.0.1"),
            port=int(self.config.get("port", 1865)),
            user_id=self.config.get("user_id", "testing_user"),
            timeout=int(self.config.get("timeout", 60)),
        )

    def connect_client(self) -> None:
        self.client.connect(
            username=self.config.get("username", "admin"),
            password=self.config.get("password", "admin"),
        )

        try:
            self.client.clean_memory()
        except AuthenticationException as e:
            self.logger.error("Connection error: %s", e)
        except ValueError as e:
            self.logger.error("Value error: %s", e)
        except GenericRequestException as e:
            self.logger.error("An unexpected error occurred: %s", e)

    def execute_run(self) -> RunResults:
        run_results: RunResults = []
        for i, conversation in enumerate(self.config.get("conversations", [])):
            self.logger.info("Conversation %s", i + 1)

            conversation_results = {}
            for llm_settings in self.config.get("llm_config", []):
                llm_settings = LLMOpenAIChatConfig.from_json(llm_settings)
                self.client.set_llm(llm_settings)
                model_name = llm_settings.model_name

                self.logger.debug("Using LLM: %s", model_name)

                conversation_results[model_name] = 0.0
                elapsed_time_message = 0.0
                for message in conversation:
                    message_text, elapsed_time_message = time_ms(self.client.send_message, message=message)
                    conversation_results[model_name] += elapsed_time_message
                    self.logger.debug("Response (%.2f ms): %s", elapsed_time_message, message_text)
                self.logger.debug("Total time: %.2f ms", conversation_results[model_name])
                self.client.clean_memory()
            run_results.append(conversation_results)
        return run_results

    def print_average_run_times(self, results: list[RunResults]) -> None:
        # Calculate averages for each model in each conversation across runs
        num_runs = len(results)
        if num_runs == 0:
            self.logger.warning("No runs were completed. Cannot calculate averages.")
        else:
            # Check if we have conversations in the results
            if len(results[0]) == 0:
                self.logger.warning("No conversations were recorded in the runs.")
            else:
                num_conversations = len(results[0])
                self.logger.info("----- AVERAGE TIMES ACROSS %d RUNS -----", num_runs)

                # Get all unique model names from the first run
                model_names: set[str] = set()
                for conv in results[0]:
                    model_names.update(conv.keys())

                # Calculate average for each model in each conversation
                for i in range(num_conversations):
                    self.logger.info("Conversation %d averages:", i + 1)
                    for model in model_names:
                        # Sum times for this model in this conversation across all runs
                        total_time = sum(results[run][i][model] for run in range(num_runs))
                        avg_time = total_time / num_runs
                        self.logger.info("  %s: %.2f ms", model, avg_time)

    def run(self) -> None:
        try:
            self.connect_client()
            results: list[RunResults] = []
            for i in range(self.config.get("num_runs", 1)):
                self.logger.info("----- RUN #%i -----", i + 1)
                results.append(self.execute_run())
            self.logger.debug(results)
            self.print_average_run_times(results)
        except KeyboardInterrupt:
            self.logger.info("Benchmark interrupted by user")
        finally:
            if hasattr(self, "client") and self.client:
                self.client.close()


def main() -> None:
    runner = BenchmarkRunner()
    runner.run()


if __name__ == "__main__":
    main()
