from kibcat_api import (
    NotCertifiedKibana,
    get_spaces,
    get_dataviews,
    get_fields_list,
    group_fields,
    get_field_properties,
    get_field_possible_values,
)

URL = "http://kibana-logging-devops-pcto.stella.cloud.az.cgm.ag"
USERNAME = "kibana"
PASSWORD = "kibanaPassword"

SPACE_ID = "default"
DATA_VIEW_ID = "container-log*"


if __name__ == "__main__":
    kibana = NotCertifiedKibana(base_url=URL, username=USERNAME, password=PASSWORD)

    spaces = get_spaces(kibana)

    if (not spaces) or (not any(space["id"] == SPACE_ID for space in spaces)):
        print("Specified space ID not found")
        exit(1)

    data_views = get_dataviews(kibana)

    if (not data_views) or (not any(view["id"] == DATA_VIEW_ID for view in data_views)):
        print("Specified data view not found")
        exit(1)

    fields_list = get_fields_list(kibana, SPACE_ID, DATA_VIEW_ID)

    if not fields_list:
        print("Not found fields_list")
        exit(1)

    grouped_list = group_fields(fields_list)

    field_name = "cometa.log.level"  # Random field just to test if everything works
    field_properties = get_field_properties(fields_list, field_name)

    values = get_field_possible_values(kibana, SPACE_ID, DATA_VIEW_ID, field_properties)

    print(values)
