"""
Pydantic models for ChatMind API
"""

from typing import Any, Optional
from pydantic import BaseModel


class ApiResponse(BaseModel):
    """Standard API response model"""
    data: Any
    message: str
    error: Optional[str] = None 