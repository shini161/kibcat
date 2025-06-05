"""
This package provides tools for grouping, cleaning, and flattening
Elasticsearch field values, with a focus on hierarchical field names.
"""

from .fields import get_initial_part_of_fields

__all__ = ["get_initial_part_of_fields"]
