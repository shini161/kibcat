from typing import Any, Type, cast

import requests
from kibana_api import Kibana

from kiblog import BaseLogger


class NotCertifiedKibana(Kibana):  # type: ignore[misc]
    """
    Kibana API client wrapper that disables SSL certificate verification and adds
    simplified methods for GET and POST requests.

    Provides methods to retrieve spaces, data views, fields list, and possible values
    for fields with optional logging.

    Inherits from the base Kibana class.
    """

    # Some types are ignored here, that's because the Kibana base class does not have Typings
    def requester(self, **kwargs: Any) -> requests.Response:
        """
        Send an HTTP request to Kibana API with SSL verification disabled.

        Args:
            **kwargs: Arguments passed to `requests.request`, such as method, url, json, etc.

        Returns:
            requests.Response: The response object from the HTTP request.
        """

        headers = (
            {
                "Content-Type": "application/json",
                "kbn-xsrf": "True",
            }
            if "files" not in kwargs
            else {"kbn-xsrf": "True"}
        )
        auth: tuple[str, str] | None = (self.username, self.password) if (self.username and self.password) else None
        return requests.request(headers=headers, auth=auth, verify=False, timeout=10, **kwargs)

    def get(self, path: str) -> requests.Response:
        """
        Send a GET request to the specified Kibana API path.

        Args:
            path (str): The API endpoint path, relative to the base URL.

        Returns:
            requests.Response: The response object from the GET request.
        """
        return self.requester(method="GET", url=f"{self.base_url}{path}")

    def post(self, path: str, body: dict[str, Any]) -> requests.Response:
        """
        Send a POST request with a JSON body to the specified Kibana API path.

        Args:
            path (str): The API endpoint path, relative to the base URL.
            body (dict[str, Any]): The JSON-serializable body payload.

        Returns:
            requests.Response: The response object from the POST request.
        """
        return self.requester(method="POST", url=f"{self.base_url}{path}", json=body)

    def get_spaces(self, logger: Type[BaseLogger] | None = None) -> list[dict[str, Any]] | None:
        """
        Retrieve the list of Kibana spaces.

        Args:
            logger (Type[BaseLogger] | None): Optional logger for info and error messages.

        Returns:
            list[dict[str, Any]] | None: List of spaces as dictionaries if successful, else None.
        """

        try:
            response: requests.Response = self.space().all()
            if response.status_code == 200:
                spaces = response.json()
                if logger:
                    logger.message("[kibapi.NotCertifiedKibana.get_spaces] - Connected to Kibana API")
                    logger.message("[kibapi.NotCertifiedKibana.get_spaces] - Available spaces:")
                    for space in spaces:
                        logger.message(f"- ID: {space['id']}, Name: {space['name']}")
                return cast(list[dict[str, Any]] | None, spaces)
            msg = f"[kibapi.NotCertifiedKibana.get_spaces] - Unexpected status code: {response.status_code}"
            if logger:
                logger.error(msg)
            return None
        except requests.RequestException as e:
            msg = f"[kibapi.NotCertifiedKibana.get_spaces]: Exception while getting spaces.\n{e}"
            if logger:
                logger.error(msg)
            return None

    def get_dataviews(self, logger: Type[BaseLogger] | None = None) -> list[dict[str, Any]] | None:
        """
        Retrieve all available data views.

        Args:
            logger (Type[BaseLogger] | None): Optional logger for info and error messages.

        Returns:
            list[dict[str, Any]] | None: List of data views as dictionaries if successful, else None.
        """

        try:
            response = self.get("/api/data_views")
            if response.status_code == 200:
                return cast(list[dict[str, Any]] | None, response.json().get("data_view", []))
            msg = f"[kibapi.NotCertifiedKibana.get_dataviews] - Can't get data views - Code {response.status_code}"
            if logger:
                logger.error(msg)
            return None
        except requests.RequestException as e:
            msg = f"[kibapi.NotCertifiedKibana.get_dataviews] - Exception while getting dataviews.\n{e}"
            if logger:
                logger.error(msg)
            return None

    def get_fields_list(
        self,
        space_id: str,
        data_view_id: str,
        logger: Type[BaseLogger] | None = None,
    ) -> list[dict[str, Any]] | None:
        """
        Retrieve the list of fields for a specified space and data view.

        Args:
            space_id (str): The ID of the Kibana space.
            data_view_id (str): The ID or pattern of the data view.
            logger (Type[BaseLogger] | None): Optional logger for info and error messages.

        Returns:
            list[dict[str, Any]] | None: List of fields as dictionaries if successful, else None.
        """

        try:
            url = f"/s/{space_id}/internal/data_views/fields?pattern={data_view_id}"
            response = self.get(url)
            if response.status_code == 200:
                return cast(list[dict[str, Any]] | None, response.json().get("fields", []))
            msg = f"[kibapi.NotCertifiedKibana.get_fields_list] - Unexpected status code: {response.status_code}"
            if logger:
                logger.error(msg)
            return None
        except requests.RequestException as e:
            msg = f"[kibapi.NotCertifiedKibana.get_fields_list] - Exception while getting fields list.\n{e}"
            if logger:
                logger.error(msg)
            return None

    # pylint: disable=too-many-positional-arguments
    def get_field_possible_values(
        self,
        space_id: str,
        data_view_id: str,
        field_dict: dict[str, Any],
        start_date: str | None = None,
        end_date: str | None = None,
        logger: Type[BaseLogger] | None = None,
    ) -> list[Any]:
        """
        Retrieve suggested possible values for a given field within a space and data view,
        optionally filtered by a date range.

        Args:
            space_id (str): The ID of the Kibana space.
            data_view_id (str): The ID of the data view.
            field_dict (dict[str, Any]): Dictionary describing the field (name, type, etc.).
            start_date (str | None): ISO 8601 formatted start date for filtering (inclusive).
            end_date (str | None): ISO 8601 formatted end date for filtering (inclusive).
            logger (Type[BaseLogger] | None): Optional logger for info and error messages.

        Returns:
            list[Any]: List of suggested field values, empty if none or on error.
        """

        if not field_dict:
            return []

        request_body: dict[str, Any] = {
            "query": "",
            "field": field_dict["name"],
            "fieldMeta": {
                "count": 1,
                "name": field_dict["name"],
                "type": field_dict["type"],
                "esTypes": field_dict["esTypes"],
                "scripted": False,
                "searchable": field_dict["searchable"],
                "aggregatable": field_dict["aggregatable"],
                "readFromDocValues": field_dict["readFromDocValues"],
                "shortDotsEnable": False,
                "isMapped": True,
            },
            "filters": (
                [
                    {
                        "range": {
                            "@timestamp": {
                                "format": "strict_date_optional_time",
                                "gte": start_date,
                                "lte": end_date,
                            }
                        }
                    }
                ]
                if start_date and end_date
                else []
            ),
            "method": "terms_enum",
        }

        try:
            api_url = f"/s/{space_id}/internal/kibana/suggestions/values/{data_view_id}"
            response = self.post(path=api_url, body=request_body)
            if response.status_code == 200:
                return cast(list[Any], response.json())

            msg = (
                "[kibapi.NotCertifiedKibana.get_field_possible_values] - "
                f"Unexpected status code: {response.status_code}"
            )
            if logger:
                logger.error(msg)
            return []
        except requests.RequestException as e:
            msg = (
                "[kibapi.NotCertifiedKibana.get_field_possible_values] - "
                f"Exception while getting field possible values.\n{e}"
            )
            if logger:
                logger.error(msg)
            return []
