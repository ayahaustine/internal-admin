"""
Internal Admin Framework

A reusable, installable administrative framework for FastAPI applications.

Public API:
- AdminSite: Central orchestrator for admin functionality
- ModelAdmin: Base class for model-specific admin configuration
- AdminConfig: Configuration container for admin settings
"""

__version__ = "0.1.0"
__author__ = "Internal Admin Team"

from .config import AdminConfig
from .site import AdminSite
from .admin.model_admin import ModelAdmin

__all__ = [
    "AdminSite",
    "ModelAdmin", 
    "AdminConfig",
]