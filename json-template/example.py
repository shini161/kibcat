from load_template import render_dict
import sys
import os

# fmt:off

# Need to add the path to import relative. Necessary only when testing here.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logger.base_logger import BaseKibCatLogger
from url_jsonifier.utils import build_rison_url_from_json

# fmt:on

# For testing
if __name__ == "__main__":
    base_url = "https://kibana-logging-devops-pcto.stella.cloud.az.cgm.ag/app/discover"
    start_time = "2025-05-09T18:02:40.258Z"
    end_time = "2025-05-10T02:05:46.064Z"
    visible_fields = ["agent.id", "cometa.log.message", "kubernetes.namespace",
                      "kubernetes.pod.name", "container.image.name", "cometa.log.level"]
    filters = [("kubernetes.namespace", "qa"),
               ("cometa.log.level", "ERROR")]
    data_view_id = "container-log*"
    search_query = "kubernetes.pod.name : \\\"backend\\\""

    result_dict = render_dict(base_url,
                              start_time,
                              end_time,
                              visible_fields,
                              filters,
                              data_view_id,
                              search_query)

    url = build_rison_url_from_json(json_dict=result_dict)

    BaseKibCatLogger.message(f"Generated URL:\n{url}")
