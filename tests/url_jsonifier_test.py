# tests/test_utils.py

import os
import json
import pytest
from url_jsonifier.utils import parse_rison_url_to_json, build_rison_url_from_json

KIBANA_URL = (
    "https://***REMOVED***/app/discover#/?"
    "_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:'2025-05-09T18:02:40.258Z',to:'2025-05-10T02:05:46.064Z'))&_a="
    "(columns:!(agent.id,***REMOVED***,***REMOVED***,***REMOVED***),"
    "dataSource:(dataViewId:'container-log*',type:dataView),filters:!(),"
    "grid:(columns:('@timestamp':(width:127),agent.id:(width:159),***REMOVED***:(width:249),"
    "***REMOVED***:(width:202))),interval:auto,"
    "query:(language:kuery,query:'***REMOVED***%20:%20%22backend%22'),"
    "sort:!(!('@timestamp',desc)))"
)

EXPECTED_OUTPUT = {
  "base_url": "https://***REMOVED***/app/discover",
  "_g": {
    "filters": [],
    "refreshInterval": {
      "pause": True,
      "value": 60000
    },
    "time": {
      "from": "2025-05-09T18:02:40.258Z",
      "to": "2025-05-10T02:05:46.064Z"
    }
  },
  "_a": {
    "columns": [
      "agent.id",
      "***REMOVED***",
      "***REMOVED***",
      "***REMOVED***"
    ],
    "dataSource": {
      "dataViewId": "container-log*",
      "type": "dataView"
    },
    "filters": [],
    "grid": {
      "columns": {
        "@timestamp": {
          "width": 127
        },
        "agent.id": {
          "width": 159
        },
        "***REMOVED***": {
          "width": 249
        },
        "***REMOVED***": {
          "width": 202
        }
      }
    },
    "interval": "auto",
    "query": {
      "language": "kuery",
      "query": "***REMOVED*** : \"backend\""
    },
    "sort": [
      [
        "@timestamp",
        "desc"
      ]
    ]
  }
}

@pytest.fixture
def temp_json_path(tmp_path):
    # Create a temp data file inside pytest's temp folder
    return tmp_path / "decode.json"

def test_parse_and_rebuild_rison_url(temp_json_path):
    parsed = parse_rison_url_to_json(KIBANA_URL, temp_json_path)
    rebuilt = build_rison_url_from_json(temp_json_path)

    assert parsed == EXPECTED_OUTPUT

    # Make sure base URL is preserved
    assert parsed["base_url"] in rebuilt

    # Optional: Check critical _g/_a keys exist in parsed result
    assert parsed["_g"] is not None
    assert parsed["_a"] is not None

    # Optional: Re-parse rebuilt and check it's same as original
    reparsed = parse_rison_url_to_json(rebuilt, temp_json_path)
    assert reparsed["_g"] == parsed["_g"]
    assert reparsed["_a"] == parsed["_a"]

