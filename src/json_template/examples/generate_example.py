from load_template import render_dict
from ...logging.base_logger import BaseKibCatLogger
from ...url_jsonifier.builders import build_rison_url_from_json


BASE_URL = "https://localhost:9200/discover"
START_TIME = "2025-05-09T18:02:40.258Z"
END_TIME = "2025-05-10T02:05:46.064Z"
VISIBLE_FIELDS = ["choco.id", "log.message", "example.namespace",
                    "example.name", "img.name", "log.level"]
FILTERS = [("example.namespace", "qa"),
            ("log.level", "ERROR")]
DATA_VIEW_ID = "logs*"
SEARCH_QUERY = "example.name : \\\"backend\\\""

LOGGER = BaseKibCatLogger

try:
    result_dict = render_dict(BASE_URL,
                            START_TIME,
                            END_TIME,
                            VISIBLE_FIELDS,
                            FILTERS,
                            DATA_VIEW_ID,
                            SEARCH_QUERY,
                            LOGGER=LOGGER)
except Exception as e:
    msg = f"generate_example.py - Failed to render dict.\n{e}"
    if LOGGER:
        LOGGER.error(msg)
    raise Exception(msg)

try:
    url = build_rison_url_from_json(json_dict=result_dict)
except Exception as e:
    msg = f"generate_example.py - Failed to build Rison URL.\n{e}"
    if LOGGER:
        LOGGER.error(msg)
    raise Exception(msg)

msg = f"generate_example.py - Generated URL:\n{url}"
LOGGER.message(msg)
