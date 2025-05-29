from jinja2 import Template
import os
import json


def render_dict(base_url,
                start_time,
                end_time,
                visible_fields,
                filters,
                data_view_id,
                search_query,
                LOGGER=None):

    if LOGGER:
        LOGGER.message("Loading template for Kibana URL")

    current_path = os.path.dirname(os.path.realpath(__file__))
    template_path = os.path.join(current_path, "url-template.json.jinja2")

    with open(template_path) as f:
        template_str = f.read()

    template = Template(template_str)

    if LOGGER:
        LOGGER.message("Template loaded")

    output_str = template.render(
        base_url=base_url,
        start_time=start_time,
        end_time=end_time,
        visible_fields=visible_fields,
        filters=filters,
        data_view_id=data_view_id,
        search_query=search_query
    )

    if LOGGER:
        LOGGER.message("Kibana URL template rendered")

    return json.loads(output_str)
