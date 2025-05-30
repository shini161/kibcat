from typing import Any
from src.json_template.builders import build_template


def test_build_template() -> None:
    base_url: str = "https://kibana.example.com/app/discover"
    start_time: str = "2025-05-09T18:02:40.258Z"
    end_time: str = "2025-05-10T02:05:46.064Z"
    visible_fields: list[str] = ["field1", "field2", "field3"]
    filters: list[tuple[str, str]] = [("field1", "value1"), ("field2", "value2")]
    data_view_id: str = "data-view-123"
    search_query: str = "field3 : \\\"value3\\\""

    output: dict[str, Any] = build_template(
        base_url,
        start_time,
        end_time,
        visible_fields,
        filters,
        data_view_id,
        search_query
    )

    # Top Level Keys
    assert "base_url" in output
    assert "_g" in output
    assert "_a" in output

    # URL base and time range
    assert output["base_url"] == base_url
    assert output["_g"]["time"]["from"] == start_time
    assert output["_g"]["time"]["to"] == end_time

    # Visible columns
    assert output["_a"]["columns"] == visible_fields

    # Filters
    filters_meta = output["_a"]["filters"]
    assert isinstance(filters_meta, list)
    assert len(filters_meta) == len(filters)

    for f_item, (field, val) in zip(filters_meta, filters):
        assert f_item["meta"]["field"] == field
        assert f_item["meta"]["params"]["query"] == val
        assert f_item["query"]["match_phrase"][field] == val

    # Search query
    assert output["_a"]["query"]["query"] == search_query.replace("\\", "")

