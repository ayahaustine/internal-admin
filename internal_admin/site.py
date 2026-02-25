"""
AdminSite class - Central orchestrator for Internal Admin.

The AdminSite is the main entry point for the admin framework.
It manages model registration, router generation, and FastAPI integration.
"""

import os
from typing import Any, Dict, Type, Optional
from pathlib import Path
from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from .config import AdminConfig
from .registry import get_registry
from .database.engine import initialize_engine
from .database.session import initialize_session_manager
from .auth.security import initialize_security
from .auth.routes import create_auth_router, require_auth
from .admin.model_admin import ModelAdmin
from .admin.router_factory import AdminRouterFactory


class AdminSite:
    """
    Central orchestrator for Internal Admin.
    
    AdminSite is responsible for:
    - Model registration and validation
    - Database initialization
    - Router generation and mounting
    - Template and static file management
    - FastAPI integration
    
    This is the main public API entry point.
    """
    
    def __init__(self, config: AdminConfig) -> None:
        """
        Initialize AdminSite with configuration.
        
        Args:
            config: AdminConfig instance with all settings
        """
        self.config = config
        self.registry = get_registry()
        self._initialized = False
        self._templates: Optional[Jinja2Templates] = None
        self._router_factory: Optional[AdminRouterFactory] = None
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate AdminConfig settings."""
        if not self.config.database_url:
            raise ValueError("database_url is required in AdminConfig")
        
        if not self.config.secret_key:
            raise ValueError("secret_key is required in AdminConfig")
        
        if self.config.user_model is None:
            raise ValueError("user_model is required in AdminConfig")
        
        # Validate user model
        from .auth.models import validate_user_model
        validate_user_model(self.config.user_model)
    
    def register(
        self, 
        model: Type[Any], 
        model_admin_class: Optional[Type[ModelAdmin]] = None
    ) -> None:
        """
        Register a model with the admin site.
        
        Args:
            model: SQLAlchemy model class to register
            model_admin_class: Optional ModelAdmin subclass for configuration
            
        Raises:
            ValueError: If model is invalid or already registered
        """
        if model_admin_class is not None and not issubclass(model_admin_class, ModelAdmin):
            raise ValueError("model_admin_class must be a subclass of ModelAdmin")
        
        # Register with the global registry
        self.registry.register(model, model_admin_class)
    
    def mount(self, app: FastAPI, prefix: str = "/admin") -> None:
        """
        Mount admin interface to FastAPI application.
        
        Args:
            app: FastAPI application instance
            prefix: URL prefix for admin routes (default: "/admin")
        """
        if self._initialized:
            raise RuntimeError("AdminSite already mounted to an application")
        
        # Initialize components
        self._initialize_components()
        
        # Create main admin router
        admin_router = self._create_admin_router(prefix)
        
        # Mount static files
        self._mount_static_files(app, prefix)
        
        # Include admin router
        app.include_router(admin_router)
        
        self._initialized = True
    
    def _initialize_components(self) -> None:
        """Initialize all admin components."""
        # Initialize database
        initialize_engine(self.config)
        initialize_session_manager()
        
        # Initialize security
        initialize_security(self.config)
        
        # Initialize templates
        self._initialize_templates()
        
        # Initialize router factory
        self._router_factory = AdminRouterFactory(self.config, self._templates)
    
    def _initialize_templates(self) -> None:
        """Initialize Jinja2 templates."""
        # Get template directory
        if self.config.template_path_override:
            template_dir = self.config.template_path_override
        else:
            # Use built-in templates
            package_dir = Path(__file__).parent
            template_dir = package_dir / "templates"
        
        self._templates = Jinja2Templates(directory=str(template_dir))
        
        # Add global template functions
        self._templates.env.globals.update({
            "admin_config": self.config,
        })
    
    def _create_admin_router(self, prefix: str) -> APIRouter:
        """
        Create main admin router with all endpoints.
        
        Args:
            prefix: URL prefix for admin routes
            
        Returns:
            FastAPI router with all admin endpoints
        """
        router = APIRouter(prefix=prefix, tags=["admin"])
        
        # Dashboard endpoint
        @router.get("/", response_class=HTMLResponse, name="admin_dashboard")
        async def dashboard(
            request: Request,
            user: Any = require_auth
        ) -> HTMLResponse:
            """Admin dashboard page."""
            # Get registered models for navigation
            registered_models = []
            for model_class, model_admin_class in self.registry.get_registered_models().items():
                model_admin = model_admin_class(model_class)
                
                # Check if user has view permission
                if model_admin.has_view_permission(user):
                    registered_models.append({
                        'name': model_class.__name__,
                        'name_lower': model_class.__name__.lower(),
                        'name_plural': f"{model_class.__name__}s",
                        'url': f"{prefix}/{model_class.__name__.lower()}/",
                    })
            
            context = {
                "request": request,
                "title": "Admin Dashboard",
                "registered_models": registered_models,
                "user": user,
            }
            
            return self._templates.TemplateResponse("admin/dashboard.html", context)
        
        # Include authentication routes
        auth_router = create_auth_router(self.config, self._templates)
        router.include_router(auth_router)
        
        # Create routes for each registered model
        for model_class, model_admin_class in self.registry.get_registered_models().items():
            model_admin = model_admin_class(model_class)
            model_router = self._router_factory.create_model_router(model_class, model_admin)
            router.include_router(model_router)
        
        return router
    
    def _mount_static_files(self, app: FastAPI, prefix: str) -> None:
        """
        Mount static files for admin interface.
        
        Args:
            app: FastAPI application
            prefix: URL prefix for admin routes
        """
        # Get static directory
        package_dir = Path(__file__).parent
        static_dir = package_dir / "static"
        
        if static_dir.exists():
            app.mount(
                f"{prefix}/static",
                StaticFiles(directory=str(static_dir)),
                name="admin_static"
            )
    
    def get_registered_models(self) -> Dict[Type[Any], Type[ModelAdmin]]:
        """
        Get all registered models and their admin classes.
        
        Returns:
            Dictionary mapping model classes to ModelAdmin classes
        """
        return self.registry.get_registered_models()
    
    def is_registered(self, model: Type[Any]) -> bool:
        """
        Check if a model is registered.
        
        Args:
            model: Model class to check
            
        Returns:
            True if model is registered
        """
        return self.registry.is_registered(model)
    
    def get_model_admin(self, model: Type[Any]) -> ModelAdmin:
        """
        Get ModelAdmin instance for a registered model.
        
        Args:
            model: Registered model class
            
        Returns:
            ModelAdmin instance
            
        Raises:
            ValueError: If model is not registered
        """
        if not self.is_registered(model):
            raise ValueError(f"Model {model.__name__} is not registered")
        
        model_admin_class = self.registry.get_model_admin(model)
        return model_admin_class(model)