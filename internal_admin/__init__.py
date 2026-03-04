"""
Internal Admin Framework

A reusable, installable administrative framework for FastAPI applications.

Public API:
- AdminSite: Central orchestrator for admin functionality
- ModelAdmin: Base class for model-specific admin configuration
- AdminConfig: Configuration container for admin settings
"""

from __future__ import annotations

# python-semantic-release manages this string directly.
# importlib.metadata is used as the authoritative source at runtime
# once the package is installed, so both stay in sync after a release.
__version__ = "0.1.0"

try:
    from importlib.metadata import PackageNotFoundError, version
    try:
        __version__ = version("internal-admin")
    except PackageNotFoundError:
        pass  # running from source without an editable install
except ImportError:
    pass  # Python < 3.8 fallback (shouldn't happen given requires-python)

__author__ = "Ayah Austine"

from .admin.model_admin import ModelAdmin
from .config import AdminConfig
from .site import AdminSite

__all__ = [
    "AdminSite",
    "ModelAdmin",
    "AdminConfig",
    "__version__",
]
