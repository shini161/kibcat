from typing import Any, Optional, Type, cast

import requests  # type: ignore[import-untyped]
from kibana_api import Kibana

from kiblog import BaseLogger


class NotCertifiedKibana(Kibana):  # type: ignore[misc]
    """Kibana class wrapper to disable SSL certificate, and also add a 'get' method for direct API calls"""

    # Some types are ignored here, that's because the Kibana base class does not have Typings
    def requester(self, **kwargs: Any) -> requests.Response:
        headers = (
            {
                "Content-Type": "application/json",
                "kbn-xsrf": "True",
            }
            if not "files" in kwargs
            else {"kbn-xsrf": "True"}
        )
        auth: tuple[str, str] | None = (self.username, self.password) if (self.username and self.password) else None
        return requests.request(headers=headers, auth=auth, verify=False, **kwargs)

    def get(self, path: str) -> requests.Response:
        return self.requester(method="GET", url=f"{self.base_url}{path}")

    def post(self, path: str, body: dict[str, Any]) -> requests.Response:
        return self.requester(method="POST", url=f"{self.base_url}{path}", json=body)

    def get_spaces(self, LOGGER: Optional[Type[BaseLogger]] = None) -> Optional[list[dict[str, Any]]]:
        """Gets the spaces as a list of dicts"""

        try:
            response: requests.Response = self.space().all()
            if response.status_code == 200:
                spaces = response.json()
                if LOGGER:
                    LOGGER.message("Connected to Kibana API")
                    LOGGER.message("Available spaces:")
                    for space in spaces:
                        LOGGER.message(f"- ID: {space['id']}, Name: {space['name']}")
                return cast(Optional[list[dict[str, Any]]], spaces)
            else:
                msg = f"get_spaces - Unexpected status code: {response.status_code}"
                if LOGGER:
                    LOGGER.error(msg)
                return None
        except Exception as e:
            msg = f"get_spaces: Exception while getting spaces.\n{e}"
            if LOGGER:
                LOGGER.error(msg)
            return None

    def get_dataviews(self, LOGGER: Optional[Type[BaseLogger]] = None) -> Optional[list[dict[str, Any]]]:
        """Gets all the available data views as a list of dicts"""
        try:
            response = self.get("/api/data_views")
            if response.status_code == 200:
                return cast(Optional[list[dict[str, Any]]], response.json().get("data_view", []))
            else:
                msg = f"get_dataviews - Can't get data views - Code {response.status_code}"
                if LOGGER:
                    LOGGER.error(msg)
                return None
        except Exception as e:
            msg = f"get_dataviews - Exception while getting dataviews.\n{e}"
            if LOGGER:
                LOGGER.error(msg)
            return None

    def get_fields_list(
        self,
        space_id: str,
        data_view_id: str,
        LOGGER: Optional[Type[BaseLogger]] = None,
    ) -> Optional[list[dict[str, Any]]]:
        """Gets the fields list as a list of dict"""
        try:
            url = f"/s/{space_id}/internal/data_views/fields?pattern={data_view_id}"
            response = self.get(url)
            if response.status_code == 200:
                return cast(Optional[list[dict[str, Any]]], response.json().get("fields", []))
            else:
                msg = f"get_fields_list - Unexpected status code: {response.status_code}"
                if LOGGER:
                    LOGGER.error(msg)
                return None
        except Exception as e:
            msg = f"get_fields_list - Exception while getting fields list.\n{e}"
            if LOGGER:
                LOGGER.error(msg)
            return None

    def get_field_possible_values(
        self,
        space_id: str,
        data_view_id: str,
        field_dict: dict[str, Any],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        LOGGER: Optional[Type[BaseLogger]] = None,
    ) -> list[Any]:
        """Returns a list of suggested values for a field"""
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
            response = self.post(api_url, request_body)
            if response.status_code == 200:
                return cast(list[Any], response.json())
            else:
                msg = f"get_field_possible_values - Unexpected status code: {response.status_code}"
                if LOGGER:
                    LOGGER.error(msg)
                return []
        except Exception as e:
            msg = f"get_field_possible_values - Exception while getting field possible values.\n{e}"
            if LOGGER:
                LOGGER.error(msg)
            return []
