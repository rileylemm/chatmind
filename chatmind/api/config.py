"""
Configuration management for ChatMind API
"""

import os
from typing import Dict, Any


def get_config() -> Dict[str, Any]:
    """Get configuration from environment variables"""
    return {
        "neo4j": {
            "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            "user": os.getenv("NEO4J_USER", "neo4j"),
            "password": os.getenv("NEO4J_PASSWORD", "chatmind123")
        },
        "qdrant": {
            "host": os.getenv("QDRANT_HOST", "localhost"),
            "port": os.getenv("QDRANT_PORT", "6335"),
            "collection_name": os.getenv("QDRANT_COLLECTION", "chatmind_embeddings")
        },
        "embedding": {
            "model_name": os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        },
        "api": {
            "host": os.getenv("API_HOST", "0.0.0.0"),
            "port": int(os.getenv("API_PORT", "8000")),
            "debug": os.getenv("API_DEBUG", "false").lower() == "true"
        }
    } 