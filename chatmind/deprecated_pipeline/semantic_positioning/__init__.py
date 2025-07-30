"""
Semantic Positioning Module

Handles 2D coordinate generation for topic nodes using UMAP dimensionality reduction.
This provides clean layouts for the frontend without requiring runtime calculations.
"""

from .apply_topic_layout import apply_topic_layout

__all__ = ['apply_topic_layout'] 