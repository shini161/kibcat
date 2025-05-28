import pytest

# Import from the package — no sys.path hacks needed
from json_template.load_template import render_dict

def test_render_dict_basic():
    base_url = "https://kibana.example.com/app/discover"
    start_time = "2025-05-09T18:02:40.258Z"
    end_time = "2025-05-10T02:05:46.064Z"
    visible_fields = ["field1", "field2", "field3"]
    filters = [("field1", "value1"), ("field2", "value2")]
    data_view_id = "data-view-123"
    search_query = 'field3 : "value3"'

    output = render_dict(
        base_url,
        start_time,
        end_time,
        visible_fields,
        filters,
        data_view_id,
        search_query
    )

    assert "base_url" in output
    assert "_g" in output
    assert "_a" in output

    assert output["base_url"] == base_url
    assert output["_g"]["time"]["from"] == start_time
    assert output["_g"]["time"]["to"] == end_time
    assert output["_a"]["columns"] == visible_fields

    filters_meta = output["_a"]["filters"]
    assert isinstance(filters_meta, list)
    assert len(filters_meta) == len(filters)
    for f_item, (field, val) in zip(filters_meta, filters):
        assert f_item["meta"]["field"] == field
        assert f_item["meta"]["params"]["query"] == val
        assert f_item["query"]["match_phrase"][field] == val

    assert output["_a"]["query"]["query"] == search_query

