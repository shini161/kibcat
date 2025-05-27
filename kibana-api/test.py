import requests
from kibana_api import Kibana


class NotCertifiedKibana(Kibana):
    """Kibana class wrapper to disable SSL certificate"""

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


URL = "http://***REMOVED***"
USERNAME = "kibana"
PASSWORD = "***REMOVED***"

SPACE_ID = "default"
DATA_VIEW_ID = "container-log*"

if __name__ == "__main__":

    kibana = NotCertifiedKibana(
        base_url=URL, username=USERNAME, password=PASSWORD)

    response = kibana.space().all()

    if response.status_code == 200:
        print("Connected to Kibana")

        spaces = response.json()

        print("Available spaces:")
        for space in spaces:
            print(f"- ID: {space['id']}, Name: {space['name']}")

        if not any(space["id"] == SPACE_ID for space in spaces):
            print("Specified ID not found")
            exit(1)

    else:
        print(
            f"Connected, but received unexpected status code: {response.status_code}")

    print("Getting data views")

    dataviews_response = kibana.get("/api/data_views")

    if dataviews_response.status_code == 200:
        dataviews = dataviews_response.json()

        data_views = dataviews["data_view"]
        for view in data_views:
            id = view["id"]
            print(f"- ID: {id}")

        if not any(view["id"] == DATA_VIEW_ID for view in data_views):
            print("Specified data view not found")
            exit(1)

    else:
        print(
            f"Cant get data views: {response.status_code}")

    fields_request_url = f"/s/{SPACE_ID}/internal/data_views/fields?pattern={DATA_VIEW_ID}"
    # &meta_fields=_source&meta_fields=_id&meta_fields=_index&meta_fields=_score&meta_fields=_ignored&allow_no_index=true&apiVersion=1

    fields_request = kibana.get(fields_request_url)

    if fields_request.status_code == 200:
        fields_json = fields_request.json()
        fields_list = fields_json["fields"]

        # import here just because its a test
        import json

        print(json.dumps(fields_list, indent=4))

    else:
        print(f"Error getting fields list: {fields_request.status_code}")
