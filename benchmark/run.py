import argparse
import json
import logging
import os
import re
import shutil
import sys
from datetime import datetime
from typing import Any

from benchmark.cc_bench_utils.exceptions import (
    AuthenticationException,
    GenericRequestException,
)
from benchmark.cc_bench_utils.models import (
    ConversationResult,
    ConversationResultEncoder,
    ConversationResults,
    LLMOpenAIChatConfig,
    RunResults,
)
from benchmark.cc_bench_utils.rest_api_client import CCApiClient
from benchmark.cc_bench_utils.stopwatch import time_ms

try:
    import colorama
    from colorama import Fore, Style
except ImportError:
    colorama = None


class BenchmarkRunner:
    def __init__(self) -> None:
        self.args = self.parse_args()

        self.output_filename = self.generate_savefile_name()
        # Check if output directory exists, if not create it
        self.output_dir = os.path.join("benchmark", "output")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        self.logger = self.load_logger(os.path.join(self.output_dir, f"{self.output_filename}.log"))
        self.check_tokens_usage = False
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

    def load_logger(self, log_file_path: str) -> logging.Logger:
        # Set up logging with colors

        if colorama is not None:
            colorama.init(autoreset=True)

            class ColoredFormatter(logging.Formatter):
                FORMATS = {
                    logging.DEBUG: f"{Fore.CYAN}%(levelname)s{Style.RESET_ALL} %(message)s",
                    logging.INFO: f"{Fore.GREEN}%(levelname)s{Style.RESET_ALL} %(message)s",
                    logging.WARNING: f"{Fore.YELLOW}%(levelname)s{Style.RESET_ALL} %(message)s",
                    logging.ERROR: f"{Fore.RED}%(levelname)s{Style.RESET_ALL} %(message)s",
                    logging.CRITICAL: f"{Fore.RED}{Style.BRIGHT}%(levelname)s{Style.RESET_ALL} %(message)s",
                }

                def format(self, record):
                    log_fmt = self.FORMATS.get(record.levelno)
                    formatter = logging.Formatter(log_fmt)
                    return formatter.format(record)

            log_level = getattr(logging, self.args.log_level.upper(), logging.INFO)

            # Configure root logger to avoid duplicate messages
            logging.basicConfig(level=log_level, handlers=[])

            handler = logging.StreamHandler()
            handler.setFormatter(ColoredFormatter())

            logger = logging.getLogger("benchmark")
            logger.setLevel(log_level)
            logger.propagate = False  # Prevent propagation to root logger

            # Remove any existing handlers to avoid duplicates
            for hdlr in logger.handlers[:]:
                logger.removeHandler(hdlr)

            logger.addHandler(handler)
        else:
            # Fallback to standard logging if colorama is not available
            log_level = getattr(logging, self.args.log_level.upper(), logging.INFO)
            logging.basicConfig(level=log_level, format="%(levelname)s %(message)s", handlers=[])

            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))

            logger = logging.getLogger("benchmark")
            logger.setLevel(log_level)
            logger.propagate = False  # Prevent propagation to root logger
            logger.addHandler(handler)

            logger.warning("Colorama not found. Falling back to standard logging without colors.")

        # Set up file logging in addition to console
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.DEBUG)  # Always write debug level to file
        if colorama is not None:
            file_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        else:
            file_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        logger.addHandler(file_handler)

        return logger

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
            # Load config with support for comments (JSONC)
            with open(config_file, "r", encoding="utf-8") as f:
                config_content = f.read()

            # Strip comments (both // and /* */ style)
            # Remove // comments
            config_content = re.sub(r"//.*?$", "", config_content, flags=re.MULTILINE)
            # Remove /* */ comments
            config_content = re.sub(r"/\*.*?\*/", "", config_content, flags=re.DOTALL)

            return dict(json.loads(config_content))
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
            if self.config.get("check_tokens_usage", False):
                if self.client.check_get_token_installed():
                    self.logger.debug("Token usage information is available.")
                    self.check_tokens_usage = True
                else:
                    self.logger.warning("Token usage information is not available.")
                    self.check_tokens_usage = False

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

            conversation_results: ConversationResults = {}

            for llm_settings in self.config.get("llm_config", []):
                llm_settings = LLMOpenAIChatConfig.from_json(llm_settings)
                self.client.set_llm(llm_settings)
                model_name = llm_settings.model_name

                self.logger.debug("Using LLM: %s", model_name)

                conversation_results[model_name] = ConversationResult(time=0.0)
                elapsed_time_message = 0.0
                for message in conversation:
                    if "%%END_FORM%%" in message:
                        self.client.send_message("Exit from form")
                    else:
                        message_text, elapsed_time_message = time_ms(self.client.send_message, message=message)

                        conversation_results[model_name].time += elapsed_time_message
                        conversation_results[model_name].response.append(message_text or "")
                        self.logger.debug("Response (%.2f ms): %s", elapsed_time_message, message_text)

                    if self.check_tokens_usage:
                        token_info = self.client.get_token_count()
                        conversation_results[model_name].input_tokens = token_info.get("input_tokens", None)
                        conversation_results[model_name].output_tokens = token_info.get("output_tokens", None)

                self.logger.debug("Total time: %.2f ms", conversation_results[model_name].time)
                self.client.clean_memory()

            run_results.append(conversation_results)

        return run_results

    def get_model_cost_by_tokens(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate the cost for a model based on input and output tokens.
        Uses the cost per million tokens from the configuration.
        """
        if not self.check_tokens_usage:
            return 0.0

        model_configs = self.config.get("llm_config", [])
        cost_per_million = {}

        # Find the config that matches the model_name
        for config in model_configs:
            if config["value"].get("model_name") == model_name:
                cost_per_million = config.get("cost_per_million_tokens", {})
                break
        input_cost = cost_per_million.get("input", 0.0)
        output_cost = cost_per_million.get("output", 0.0)

        total_cost: float = (input_tokens * input_cost + output_tokens * output_cost) / 1_000_000
        return total_cost

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
                        total_time = sum(results[run][i][model].time for run in range(num_runs))
                        avg_time = total_time / num_runs

                        # Calculate average token usage (handling None values)
                        avg_input = sum(results[run][i][model].input_tokens or 0 for run in range(num_runs)) / num_runs
                        avg_output = (
                            sum(results[run][i][model].output_tokens or 0 for run in range(num_runs)) / num_runs
                        )

                        # Format token info only if not zero
                        token_info = ""
                        if avg_input > 0 or avg_output > 0:
                            token_info = f" (avg tokens: {int(avg_input)} input, {int(avg_output)} output)"
                        cost = self.get_model_cost_by_tokens(model, int(avg_input), int(avg_output))
                        if cost > 0:
                            token_info += f", cost: ${cost:.6f}"

                        self.logger.info("  %s: %.2f ms%s", model, avg_time, token_info)

    def generate_savefile_name(self) -> str:
        """
        Generate a save file name based on the current date and time.
        The format is 'benchmark_YYYYMMDD_HHMMSS'.
        """
        now = datetime.now()
        return f"benchmark_{now.strftime('%Y%m%d_%H%M%S')}"

    def run(self) -> None:
        results: list[RunResults] = []
        self.logger.info("Starting benchmark runs. Results will be saved to '%s'.", self.output_filename)
        try:
            self.connect_client()

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

            # If results is not empty, save to file
            if results:
                output_file = os.path.join(self.output_dir, f"{self.output_filename}.json")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=4, cls=ConversationResultEncoder)
                self.logger.info("Results saved to '%s'", output_file)
            else:
                self.logger.warning("No results to save.")


def main() -> None:
    runner = BenchmarkRunner()
    runner.run()


if __name__ == "__main__":
    main()
