from jinja2 import Template
import os
import sys
import json

# Do this to import from relative path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from url_jsonifier.utils import build_rison_url_from_json

def render_dict(base_url,
                start_time,
                end_time,
                visible_fields,
                filters,
                data_view_id,
                search_query):

    current_path = os.path.dirname(os.path.realpath(__file__))
    template_path = os.path.join(current_path, "url-template.json.jinja2")

    with open(template_path) as f:
        template_str = f.read()

    template = Template(template_str)

    output_str = template.render(
        base_url=base_url,
        start_time=start_time,
        end_time=end_time,
        visible_fields=visible_fields,
        filters=filters,
        data_view_id=data_view_id,
        search_query=search_query
    )

    return json.loads(output_str)


# For testing
if __name__ == "__main__":
    base_url = "https://***REMOVED***/app/discover"
    start_time = "2025-05-09T18:02:40.258Z"
    end_time = "2025-05-10T02:05:46.064Z"
    visible_fields = ["agent.id", "***REMOVED***", "***REMOVED***",
                      "***REMOVED***", "container.image.name", "***REMOVED***"]
    filters = [("***REMOVED***", "qa"),
               ("***REMOVED***", "ERROR")]
    data_view_id = "container-log*"
    search_query = "***REMOVED*** : \\\"backend\\\""

    result_dict = render_dict(base_url,
                              start_time,
                              end_time,
                              visible_fields,
                              filters,
                              data_view_id,
                              search_query)

    url = build_rison_url_from_json(json_dict=result_dict)

    print(url)
