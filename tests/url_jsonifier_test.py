# tests/test_utils.py

import os
import json
import pytest
from url_jsonifier.utils import parse_rison_url_to_json, build_rison_url_from_json

KIBANA_URLS = [
    (
        # Original -> MEDIUM COMPLEXITY
        "https://***REMOVED***/app/discover#/?"
        "_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:'2025-05-09T18:02:40.258Z',to:'2025-05-10T02:05:46.064Z'))&_a="
        "(columns:!(agent.id,***REMOVED***,***REMOVED***,***REMOVED***),"
        "dataSource:(dataViewId:'container-log*',type:dataView),filters:!(),"
        "grid:(columns:('@timestamp':(width:127),agent.id:(width:159),***REMOVED***:(width:249),"
        "***REMOVED***:(width:202))),interval:auto,"
        "query:(language:kuery,query:'***REMOVED***%20:%20%22backend%22'),"
        "sort:!(!('@timestamp',desc)))"

    ),
    (
        # MINIMAL COMPLEXITY
        "https://***REMOVED***/app/discover#/?_g="
        "(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:'2025-05-04T20:43:12.758Z',to:'2025-05-08T03:47:54.786Z'))&_a="
        "(columns:!(agent.id),dataSource:(dataViewId:'container-log*',type:dataView),filters:!(('$state':(store:appState),"
        "meta:(alias:!n,disabled:!f,field:agent.id,index:'container-log*',key:agent.id,negate:!f,params:(query:'93dc8a23'),type:phrase),"
        "query:(match_phrase:(agent.id:'93dc8a23')))),interval:auto,query:(language:kuery,query:''),sort:!(!('@timestamp',desc)))"
    ),
    (
        # EMPTY FILTERS AND NESTED ARRAY
        "https://***REMOVED***/app/discover#/?_g="
        "(filters:!(),refreshInterval:(pause:!f,value:30000),time:(from:'2025-05-01T00:00:00.001Z',to:'2025-05-28T05:29:14.652Z'))&_a="
        "(columns:!(host,message),dataSource:(dataViewId:'container-log*',type:dataView),filters:!(),interval:auto,query:(language:kuery,query:''),sort:!(!(host,asc)))"
    ),
    (
        # UNUSUAL BUT VALID RISON SYNTAX
        "https://***REMOVED***/app/discover#/?_g="
        "(refreshInterval:(pause:!f,value:null),time:(from:'2025-05-01T00:00:00.001Z',to:'2025-05-28T05:29:14.652Z'))&_a="
        "(query:(language:'lucene',query:''),filters:!(),columns:!())"
    )
]

EXPECTED_OUTPUT_1 = {
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


@pytest.mark.parametrize("url", KIBANA_URLS)
def test_parse_and_rebuild_rison_url(url, tmp_path):
    json_path = tmp_path / "parsed.json"
    parsed = parse_rison_url_to_json(url, json_path)
    assert "base_url" in parsed
    assert parsed["base_url"].startswith("https://***REMOVED***")

    if "_g" in parsed:
        assert isinstance(parsed["_g"], dict)
    if "_a" in parsed:
        assert isinstance(parsed["_a"], dict)

    rebuilt = build_rison_url_from_json(json_path)
    assert parsed["base_url"] in rebuilt

    reparsed = parse_rison_url_to_json(rebuilt, json_path)

    if "_g" in parsed:
        assert reparsed["_g"] == parsed["_g"]
    if "_a" in parsed:
        assert reparsed["_a"] == parsed["_a"]

    # Extra check only for the first URL
    if url == KIBANA_URLS[0]:
        assert parsed == EXPECTED_OUTPUT_1
