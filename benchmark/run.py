import argparse
import json
import os
import shutil
import sys

from benchmark.cc_bench_utils import AuthenticationException, CCApiClient, GenericRequestException


def main() -> None:
    parser = argparse.ArgumentParser(description="Cheshire Cat API Chat Script")
    parser.add_argument(
        "--config-file", type=str, default="benchmark/config.json", help="Path to config file (default: config.json)"
    )
    args = parser.parse_args()

    config_file = args.config_file
    example_file = os.path.join(os.path.dirname(config_file), "config.example.json")

    # If config file is missing or empty, copy from example
    if not os.path.exists(config_file) or os.path.getsize(config_file) == 0:
        if os.path.exists(example_file):
            shutil.copyfile(example_file, config_file)
            print(f"Info: '{config_file}' was missing or empty. Copied from '{example_file}'.")
        else:
            print(f"Error: Config file '{config_file}' not found and no example config present.")
            sys.exit(1)

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON in '{config_file}': {e}")
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
        print(f"Connection error: {e}")
    except ValueError as e:
        print(f"Value error: {e}")
    except GenericRequestException as e:
        print(f"An unexpected error occurred: {e}")

    for i, conversation in enumerate(config.get("conversations", [])):
        print(f"Conversation {i + 1}:")
        for llm_settings in config.get("llm_config", []):
            client.set_llm(llm_settings)
            for message in conversation:
                print(client.send_message(message=message))
    client.close()


if __name__ == "__main__":
    main()
