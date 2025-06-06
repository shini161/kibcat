from kibtemplate import FilterOperators, KibCatFilter, build_template
from kibtypes import ParsedKibanaURL

# Params for building template
BASE_URL = "https://kibana.example.com/app/discover"
START_TIME = "2025-05-09T18:02:40.258Z"
END_TIME = "2025-05-10T02:05:46.064Z"
VISIBLE_FIELDS: list[str] = ["field1", "field2", "field3"]
FILTERS: list[KibCatFilter] = [
    KibCatFilter("field1", FilterOperators.IS, "value1"),
    KibCatFilter("field2", FilterOperators.IS, "value2"),
]
DATA_VIEW_ID = "data-view-123"
SEARCH_QUERY = 'field3 : \\"value3\\"'


def test_kibcat_filter() -> None:
    """Verify that KibCatFilter can be initialized and serialized correctly."""

    # Create a filter instance
    filter_instance = KibCatFilter(field="field1", operator=FilterOperators.IS, value="value1")

    # Check attributes
    assert filter_instance.field == "field1"
    assert filter_instance.operator == FilterOperators.IS
    assert filter_instance.value == "value1"

    # Serialize to JSON
    json_output = filter_instance.model_dump()
    assert json_output["field"] == "field1"
    assert json_output["operator"] == "IS"
    assert json_output["value"] == "value1"

    assert FilterOperators.IS.value == 1
    assert FilterOperators.IS.name == "IS"
    assert FilterOperators["IS"].value == 1


def test_build_template() -> None:
    """Verify that build_template correctly constructs the Kibana URL JSON structure."""

    output: ParsedKibanaURL = build_template(
        base_url=BASE_URL,
        start_time=START_TIME,
        end_time=END_TIME,
        visible_fields=VISIBLE_FIELDS,
        filters=FILTERS,
        data_view_id=DATA_VIEW_ID,
        search_query=SEARCH_QUERY,
    )

    # Top Level Keys
    assert "base_url" in output
    assert "_g" in output
    assert "_a" in output
    assert output["_g"] is not None
    assert output["_a"] is not None

    # URL base and time range
    assert output["base_url"] == BASE_URL
    assert output["_g"]["time"]["from"] == START_TIME
    assert output["_g"]["time"]["to"] == END_TIME

    # Visible columns
    assert output["_a"]["columns"] == VISIBLE_FIELDS

    # Filters
    filters_meta = output["_a"]["filters"]
    assert isinstance(filters_meta, list)
    assert len(filters_meta) == len(FILTERS)

    for f_item, filterkib in zip(filters_meta, FILTERS):
        assert f_item["meta"]["field"] == filterkib.field
        assert f_item["meta"]["params"]["query"] == filterkib.value
        assert f_item["query"]["match_phrase"][filterkib.field] == filterkib.value

    # Search query
    assert output["_a"]["query"]["query"] == SEARCH_QUERY.replace("\\", "")
