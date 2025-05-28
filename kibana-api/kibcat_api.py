from typing import List, Dict
import requests
from collections import defaultdict
from kibana_api import Kibana


class NotCertifiedKibana(Kibana):
    """Kibana class wrapper to disable SSL certificate, and also add a get method for direct API calls"""

    def requester(self, **kwargs):
        headers = {
            "Content-Type": "application/json",
            "kbn-xsrf": "True",
        } if not "files" in kwargs else {
            "kbn-xsrf": "True",
        }
        auth = (self.username, self.password) if (
            self.username and self.password) else None
        return requests.request(headers=headers, auth=auth, verify=False, **kwargs)

    def get(self, path):
        return self.requester(method="GET", url=f"{self.base_url}{path}")

    def post(self, path, body):
        return self.requester(method="POST", url=f"{self.base_url}{path}", json=body)


def group_fields(fields: List) -> List:
    """Groups fields with their specific keyword, in a list, for example the output might be:
    [[
        "stream",
        "stream.keyword"
    ],
    [
        "tags",
        "tags.keyword"
    ]]"""
    groups_dict = defaultdict(list)

    for field in fields:
        # Get field name
        name = field["name"]

        # Get field parent if it exists
        sub_type = field.get("subType", {})
        multi = sub_type.get("multi", {})
        parent = multi.get("parent")

        if parent:
            groups_dict[parent].append(name)

    grouped = set()
    result = []

    for field in fields:
        name = field["name"]

        if name in groups_dict:
            group = [name] + groups_dict[name]
            result.append(group)
            grouped.update(group)

        elif name not in grouped:
            result.append([name])
            grouped.add(name)

    return result


def get_field_properties(fields: List, target_field: str) -> Dict:
    return next((d for d in fields if d["name"] == target_field), None)


def get_spaces(kibana: Kibana) -> List | None:
    """Gets the spaces as a list of dicts"""
    response = kibana.space().all()

    if response.status_code == 200:
        print("Connected to Kibana")

        spaces = response.json()

        print("Available spaces:")
        for space in spaces:
            print(f"- ID: {space['id']}, Name: {space['name']}")

        return spaces

    else:
        print(
            f"Connected, but received unexpected status code: {response.status_code}")
        return None


def get_dataviews(kibana: NotCertifiedKibana) -> List | None:
    """Gets all the available data views as a list of dicts"""
    dataviews_response = kibana.get("/api/data_views")

    if dataviews_response.status_code == 200:
        dataviews = dataviews_response.json()

        data_views = dataviews["data_view"]
        return data_views

    else:
        print(
            f"Cant get data views: {dataviews_response.status_code}")
        return None


def get_fields_list(kibana: NotCertifiedKibana, space_id: str, data_view_id: str) -> List | None:
    """Gets the fields list as a list of dict"""

    fields_request_url = f"/s/{space_id}/internal/data_views/fields?pattern={data_view_id}"
    # &meta_fields=_source&meta_fields=_id&meta_fields=_index&meta_fields=_score&meta_fields=_ignored&allow_no_index=true&apiVersion=1

    fields_request = kibana.get(fields_request_url)

    if fields_request.status_code == 200:
        fields_json = fields_request.json()
        fields_list = fields_json["fields"]

        return fields_list

    else:
        print(f"Error getting fields list: {fields_request.status_code}")
        return None


def get_field_possible_values(kibana: NotCertifiedKibana, space_id: str, data_view_id: str, field_dict: Dict, start_date: str | None = None, end_date: str | None = None) -> List | None:
    request_body = {
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
            "isMapped": True
        },
        "filters": [{
            "range": {
                "@timestamp": {
                    "format": "strict_date_optional_time",
                    "gte": start_date,
                    "lte": end_date
                }
            }
        }] if start_date and end_date else [],
        "method": "terms_enum"
    }

    api_url = f"/s/{space_id}/internal/kibana/suggestions/values/{data_view_id}"
    response = kibana.post(api_url, request_body)

    if response.status_code == 200:
        return response.json()
    else:
        print(
            f"Error getting the fields possible values: {response.status_code}")
        return None
