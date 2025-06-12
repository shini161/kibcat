import argparse

from benchmark.cc_bench_utils import AuthenticationError, CCApiClient, GenericRequestError


def main() -> None:
    # Configure argparse to handle command-line arguments
    parser = argparse.ArgumentParser(description="Cheshire Cat API Chat Script")
    parser.add_argument("message", type=str, help="The message to send to the server")
    parser.add_argument("--user_id", type=str, default="testing_user", help="The user ID for authentication")
    parser.add_argument(
        "--username", type=str, default="admin", help="The username for authentication (default: admin)"
    )
    parser.add_argument("--password", type=str, default="admin", help="The password for authentication")
    parser.add_argument(
        "--base_url", type=str, default="127.0.0.1", help="The base URL of the Cheshire Cat server (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=1865, help="The port number of the Cheshire Cat server (default: 1865)"
    )
    parser.add_argument("--timeout", type=int, default=60, help="Max wait time for AI response (default: 60s).")
    args = parser.parse_args()

    # Create an instance of the CCApiClient
    client = CCApiClient(base_url=args.base_url, port=args.port, user_id=args.user_id, timeout=args.timeout)
    client.connect(username=args.username, password=args.password)
    try:
        # Send the message to the server and print the response
        print(client.send_message(message=args.message))
    except AuthenticationError as e:
        print(f"Connection error: {e}")
    except ValueError as e:
        print(f"Value error: {e}")
    except GenericRequestError as e:
        # Keep this for unexpected errors, but at least we tried to catch specific ones first
        print(f"An unexpected error occurred: {e}")
    finally:
        # Close the connection
        client.close()


if __name__ == "__main__":
    main()
