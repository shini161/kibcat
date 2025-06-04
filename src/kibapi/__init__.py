"""
kibapi package

This package provides a wrapper client for interacting with the Kibana REST API,
including features such as disabling SSL verification for self-signed certificates,
convenience methods for HTTP GET and POST requests, and helpers to retrieve
spaces, data views, fields, and possible values.

The package aims to simplify automation and scripting tasks with Kibana.
"""

from .not_certified_kibana import NotCertifiedKibana
from .utils import get_field_properties, group_fields

__all__ = ["NotCertifiedKibana", "get_field_properties", "group_fields"]
