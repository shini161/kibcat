import json
import sys
import threading
import time
from typing import Any, Dict, Optional

import requests

try:
    from cheshire_cat_api.cat_client import CatClient
    from cheshire_cat_api.config import Config as CatClientConfig
except ImportError:
    print("Cheshire Cat API client not found. Please install the cheshire_cat_api package.")
    print("You can install it using: pip install -r benchmark/requirements.txt")
    sys.exit(1)

from .exceptions import AuthenticationException, GenericRequestException
from .models import LLMOpenAIChatConfig


class CCApiClient:
    """
    A client for the Cheshire Cat REST API.

    This client provides methods to interact with the Cheshire Cat server
    using GET and POST requests, with authentication support.
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        base_url: str = "localhost",
        port: int = 1865,
        user_id: str = "testing_user",
        timeout: int = 10,
    ):
        """
        Initialize the Cheshire Cat REST API client.

        Args:
            base_url (str): The base URL of the server (default: localhost)
            port (int): The port number of the server (default: 1865)
            user_id (str): The user ID for authentication (default: testing_user)
            timeout (int): The timeout for waiting for responses (default: 10 seconds)
        """
        self.base_url = base_url
        self.port = port
        self.user_id = user_id
        self.timeout = timeout
        self.auth_token: str | None = None
        self.base_api_url = f"http://{base_url}:{port}"
        self.cat_client: Any = None

        self._message_completed = threading.Event()
        self._last_message = None

    def obtain_auth_token(self, username: str, password: str) -> str:
        """
        Obtains the authentication token (JWT token) from the Cheshire Cat server.

        Args:
            username (str): The username for authentication
            password (str): The password for authentication

        Returns:
            str: The authentication token if successful

        Raises:
            AuthenticationException: If authentication fails
        """
        auth_url = f"{self.base_api_url}/auth/token"

        headers = {"Content-Type": "application/json"}
        data = {"username": username, "password": password}

        try:
            response = requests.post(auth_url, headers=headers, json=data, timeout=self.timeout)
            response.raise_for_status()
            token_data = response.json()
            self.auth_token = token_data.get("access_token")
            if not self.auth_token:
                raise AuthenticationException("No access_token received from server.")
            return self.auth_token
        except requests.exceptions.RequestException as e:
            raise AuthenticationException(f"Authentication failed: {e}") from e

    def _wait_for_connection(self) -> None:
        """
        Waits for the WebSocket to connect within the specified timeout period.

        Raises:
            TimeoutError: If the WebSocket fails to connect within the timeout.
        """
        start_time = time.time()
        while not (self.cat_client and getattr(self.cat_client, "is_ws_connected", False)):
            time.sleep(1)
            if time.time() - start_time > self.timeout:
                raise TimeoutError("Failed to connect to WebSocket within timeout (10 sec).")

    def _message_handler(self, message: str) -> None:
        """
        Custom handler for messages received from the WebSocket.

        Args:
            message (str): The message received from the WebSocket

        Raises:
            json.JSONDecodeError: If the message cannot be decoded as JSON
        """
        try:
            answer = json.loads(message)
            if answer.get("type") != "chat_token":  # Ignore 'chat_token' messages
                text = answer.get("text", None)
                self._last_message = text
                self._message_completed.set()
        except json.JSONDecodeError as e:
            print(f"Failed to decode message: {e}")

    def connect(self, username: str, password: str) -> str:
        """
        Connects to the Cheshire Cat server and obtains an authentication token.

        Args:
            username (str): The username for authentication
            password (str): The password for authentication

        Returns:
            str: The authentication token if successful

        Raises:
            Exception: If connection or authentication fails
        """
        self.auth_token = self.obtain_auth_token(username, password)
        if self.auth_token is None:
            raise AuthenticationException("Authentication token is None after obtain_auth_token.")
        # Create configuration using the Config class from the API
        config = CatClientConfig(
            base_url=self.base_url,
            port=self.port,
            user_id=self.user_id,
            auth_key=self.auth_token,
        )
        self.cat_client = CatClient(config=config, on_message=self._message_handler)
        self.cat_client.connect_ws()
        self._wait_for_connection()
        return self.auth_token

    def close(self) -> None:
        """
        Closes the connection to the Cheshire Cat server.

        This method should be called to clean up resources when done.
        """
        if self.cat_client:
            self.cat_client.close()
            self.cat_client = None
        else:
            print("No active connection to close.")

    def send_message(self, message: str) -> Optional[str]:
        self._message_completed.clear()
        if self.cat_client:
            self.cat_client.send(message=message)
        else:
            raise RuntimeError("No active connection to send message.")
        # Wait for the message to be fully processed or timeout
        if not self._message_completed.wait(timeout=self.timeout):
            # Throw a response timeout error if the message is not completed
            raise TimeoutError(f"Response timeout after {self.timeout} seconds for message: {message}")
        return self._last_message

    def _parse_token_count(self, response: str) -> Dict[str, int]:
        # Response from tool is similar to "Input tokens: #\nOutput tokens: #"
        try:
            token_counts = {}
            lines = response.split("\n")
            for line in lines:
                if "Input tokens:" in line:
                    token_counts["input_tokens"] = int(line.split(":")[1].strip())
                elif "Output tokens:" in line:
                    token_counts["output_tokens"] = int(line.split(":")[1].strip())
            return token_counts
        except (ValueError, IndexError) as e:
            raise GenericRequestException(f"Failed to parse token count from response: {response}") from e

    def get_token_count(self) -> Dict[str, int]:
        """
        Retrieves the token count from the Cheshire Cat, using custom plugin.

        Returns:
            Dict[str, int]: A dictionary containing 'input_tokens' and 'output_tokens'

        Raises:
            GenericRequestException: If the request fails or response is invalid
        """
        response = self.send_message("Get token count")
        if not response:
            raise GenericRequestException("No response received from 'Get tokens' endpoint.")
        return self._parse_token_count(response)

    def check_get_token_installed(self) -> bool:
        """
        Checks if the 'token_counter' plugin is active on the Cheshire Cat server.

        Returns:
            bool: True if the plugin is working, False otherwise
        """
        try:
            self.get_token_count()
            return True
        except (RuntimeError, TimeoutError, GenericRequestException):
            return False

    def _get_headers(self) -> Dict[str, str]:
        """
        Constructs the headers for API requests, including authentication if available.

        Returns:
            Dict[str, str]: Headers dictionary
        """
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        headers["user_id"] = self.user_id
        return headers

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Performs a GET request to the specified endpoint.

        Args:
            endpoint (str): The API endpoint (without the base URL)
            params (Dict[str, Any], optional): Query parameters

        Returns:
            Dict[str, Any]: JSON response from the server

        Raises:
            GenericRequestException: If the request fails
        """
        url = f"{self.base_api_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        try:
            response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            result: Dict[str, Any] = response.json()
            return result
        except requests.exceptions.RequestException as e:
            raise GenericRequestException(f"GET request failed: {e}") from e

    def _post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Performs a POST request to the specified endpoint.

        Args:
            endpoint (str): The API endpoint (without the base URL)
            data (Dict[str, Any], optional): JSON data to send
            files (Dict[str, Any], optional): Files to upload

        Returns:
            Dict[str, Any]: JSON response from the server

        Raises:
            GenericRequestException: If the request fails
        """
        url = f"{self.base_api_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        try:
            response = requests.post(url, headers=headers, json=data, files=files, timeout=self.timeout)
            response.raise_for_status()
            result: Dict[str, Any] = response.json()
            return result
        except requests.exceptions.RequestException as e:
            raise GenericRequestException(f"POST request failed: {e}") from e

    def _delete(self, endpoint: str) -> Dict[str, Any]:
        """
        Performs a DELETE request to the specified endpoint.

        Args:
            endpoint (str): The API endpoint (without the base URL)

        Returns:
            Dict[str, Any]: JSON response from the server

        Raises:
            GenericRequestException: If the request fails
        """
        url = f"{self.base_api_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        try:
            response = requests.delete(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            result: Dict[str, Any] = response.json()
            return result
        except requests.exceptions.RequestException as e:
            raise GenericRequestException(f"DELETE request failed: {e}") from e

    def _put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Performs a PUT request to the specified endpoint.

        Args:
            endpoint (str): The API endpoint (without the base URL)
            data (Dict[str, Any], optional): JSON data to send

        Returns:
            Dict[str, Any]: JSON response from the server

        Raises:
            GenericRequestException: If the request fails
        """
        url = f"{self.base_api_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        try:
            response = requests.put(url, headers=headers, json=data, timeout=self.timeout)
            response.raise_for_status()
            result: Dict[str, Any] = response.json()
            return result
        except requests.exceptions.RequestException as e:
            raise GenericRequestException(f"PUT request failed: {e}") from e

    def clean_memory(
        self,
    ) -> None:
        self._delete("/memory/conversation_history")
        self._delete("/memory/collections")

    def set_llm(self, llm_settings: LLMOpenAIChatConfig) -> None:
        """
        Sets the LLM settings for the Cheshire Cat server.

        Args:
            llm_settings (LLMOpenAIChatConfig): The LLM settings to apply

        Raises:
            GenericRequestException: If the request fails
        """
        if not isinstance(llm_settings, LLMOpenAIChatConfig):
            llm_settings = LLMOpenAIChatConfig.from_json(llm_settings)
        settings_obj = llm_settings.to_dict()
        self._put("/llm/settings/LLMOpenAIChatConfig", data=settings_obj)
