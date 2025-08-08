"""
Utility functions for ChatMind API
"""

import os
from typing import Any


def convert_neo4j_to_json(obj):
    """Convert Neo4j objects to JSON-serializable format"""
    if hasattr(obj, 'iso_format'):  # Neo4j DateTime objects
        return obj.iso_format()
    elif hasattr(obj, 'to_native'):  # Other Neo4j time objects
        return obj.to_native().isoformat()
    elif isinstance(obj, dict):
        return {k: convert_neo4j_to_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_neo4j_to_json(item) for item in obj]
    else:
        return obj


from config import get_config 