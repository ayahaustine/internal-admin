"""
Core admin engine for Internal Admin.

This module contains the main admin functionality:
- ModelAdmin base class for model configuration
- Router factory for generating CRUD routes
- Query engine for database operations
- Form engine for form generation and validation
- Filter system for list views
"""

from .model_admin import ModelAdmin
from .query_engine import QueryEngine
from .form_engine import FormEngine
from .router_factory import AdminRouterFactory

__all__ = [
    "ModelAdmin",
    "QueryEngine", 
    "FormEngine",
    "AdminRouterFactory",
]