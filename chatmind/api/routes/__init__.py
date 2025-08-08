"""
Routes package for ChatMind API
"""

from .health import router as health_router
from .search import router as search_router
from .graph import router as graph_router
from .debug import router as debug_router

__all__ = ["health_router", "search_router", "graph_router", "debug_router"] 