from pathlib import Path

import pytest

from src.kibcat_types.parsed_kibana_url import ParsedKibanaURL
from src.url_jsonifier.builders import build_rison_url_from_json
from src.url_jsonifier.parsers import parse_rison_url_to_json

KIBANA_URLS: list[str] = [
    (
        # Original -> MEDIUM COMPLEXITY
        "https://example.com/app/discover#/?"
        "_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:'2025-05-09T18:02:40.258Z',to:'2025-05-10T02:05:46.064Z'))&_a="
        "(columns:!(example.id,log.message,example.namespace,example.name),"
        "dataSource:(dataViewId:'logs*',type:dataView),filters:!(),"
        "grid:(columns:('@timestamp':(width:127),example.id:(width:159),log.message:(width:249),"
        "example.namespace:(width:202))),interval:auto,"
        "query:(language:kuery,query:'example.name%20:%20%22backend%22'),"
        "sort:!(!('@timestamp',desc)))"
    ),
    (
        # MINIMAL COMPLEXITY
        "https://example.com/app/discover#/?_g="
        "(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:'2025-05-04T20:43:12.758Z',to:'2025-05-08T03:47:54.786Z'))&_a="
        "(columns:!(example.id),dataSource:(dataViewId:'logs*',type:dataView),filters:!(('$state':(store:appState),"
        "meta:(alias:!n,disabled:!f,field:example.id,index:'logs*',key:example.id,negate:!f,params:(query:'exampleid'),type:phrase),"
        "query:(match_phrase:(example.id:'exampleid')))),interval:auto,query:(language:kuery,query:''),sort:!(!('@timestamp',desc)))"
    ),
    (
        # EMPTY FILTERS AND NESTED ARRAY
        "https://example.com/app/discover#/?_g="
        "(filters:!(),refreshInterval:(pause:!f,value:30000),time:(from:'2025-05-01T00:00:00.001Z',to:'2025-05-28T05:29:14.652Z'))&_a="
        "(columns:!(host,message),dataSource:(dataViewId:'logs*',type:dataView),filters:!(),interval:auto,query:(language:kuery,query:''),sort:!(!(host,asc)))"
    ),
    (
        # UNUSUAL BUT VALID RISON SYNTAX
        "https://example.com/app/discover#/?_g="
        "(refreshInterval:(pause:!f,value:null),time:(from:'2025-05-01T00:00:00.001Z',to:'2025-05-28T05:29:14.652Z'))&_a="
        "(query:(language:'lucene',query:''),filters:!(),columns:!())"
    ),
]

EXPECTED_OUTPUT_1: ParsedKibanaURL = {
    "base_url": "https://example.com/app/discover",
    "_g": {
        "filters": [],
        "refreshInterval": {"pause": True, "value": 60000},
        "time": {"from": "2025-05-09T18:02:40.258Z", "to": "2025-05-10T02:05:46.064Z"},
    },
    "_a": {
        "columns": ["example.id", "log.message", "example.namespace", "example.name"],
        "dataSource": {"dataViewId": "logs*", "type": "dataView"},
        "filters": [],
        "grid": {
            "columns": {
                "@timestamp": {"width": 127},
                "example.id": {"width": 159},
                "log.message": {"width": 249},
                "example.namespace": {"width": 202},
            }
        },
        "interval": "auto",
        "query": {"language": "kuery", "query": 'example.name : "backend"'},
        "sort": [["@timestamp", "desc"]],
    },
}


@pytest.mark.parametrize("url", KIBANA_URLS)
def test_parse_and_rebuild_rison_url(url: str, tmp_path: Path) -> None:
    json_path = tmp_path / "parsed.json"
    json_path_str = str(json_path)

    parsed: ParsedKibanaURL = parse_rison_url_to_json(url, json_path_str)

    assert "base_url" in parsed
    assert parsed["base_url"].startswith("https://example.com")

    if "_g" in parsed:
        assert isinstance(parsed["_g"], dict)
    if "_a" in parsed:
        assert isinstance(parsed["_a"], dict)

    rebuilt: str = build_rison_url_from_json(json_path_str)
    assert parsed["base_url"] in rebuilt

    reparsed: ParsedKibanaURL = parse_rison_url_to_json(rebuilt, json_path_str)

    if "_g" in parsed:
        assert reparsed["_g"] == parsed["_g"]
    if "_a" in parsed:
        assert reparsed["_a"] == parsed["_a"]

    if url == KIBANA_URLS[0]:
        assert parsed == EXPECTED_OUTPUT_1
