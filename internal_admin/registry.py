"""
Model registry for Internal Admin.

The registry maintains a mapping of SQLAlchemy models to their 
associated ModelAdmin classes and provides validation.
"""

from typing import Dict, Type, Any, Optional
import inspect
from sqlalchemy.ext.declarative import DeclarativeMeta


class ModelRegistry:
    """
    Registry for storing registered models and their admin classes.
    
    Responsibilities:
    - Store registered models with their ModelAdmin classes
    - Validate model metadata during registration
    - Provide access to registered model information
    """
    
    def __init__(self) -> None:
        self._registry: Dict[Type[Any], Type[Any]] = {}
    
    def register(self, model: Type[Any], model_admin_class: Optional[Type[Any]] = None) -> None:
        """
        Register a model with its ModelAdmin class.
        
        Args:
            model: SQLAlchemy model class to register
            model_admin_class: Optional ModelAdmin subclass for this model
            
        Raises:
            ValueError: If model is invalid or already registered
        """
        self._validate_model(model)
        
        if model in self._registry:
            raise ValueError(f"Model {model.__name__} is already registered")
        
        # Import here to avoid circular imports
        from .admin.model_admin import ModelAdmin
        
        # Use default ModelAdmin if none provided
        if model_admin_class is None:
            model_admin_class = ModelAdmin
        
        # Validate ModelAdmin class
        if not issubclass(model_admin_class, ModelAdmin):
            raise ValueError(f"model_admin_class must be a subclass of ModelAdmin")
        
        self._registry[model] = model_admin_class
    
    def get_model_admin(self, model: Type[Any]) -> Type[Any]:
        """Get the ModelAdmin class for a registered model."""
        if model not in self._registry:
            raise ValueError(f"Model {model.__name__} is not registered")
        return self._registry[model]
    
    def get_registered_models(self) -> Dict[Type[Any], Type[Any]]:
        """Get all registered models and their admin classes."""
        return self._registry.copy()
    
    def is_registered(self, model: Type[Any]) -> bool:
        """Check if a model is registered."""
        return model in self._registry
    
    def _validate_model(self, model: Type[Any]) -> None:
        """
        Validate that a model meets requirements for registration.
        
        Requirements:
        - Must be a SQLAlchemy declarative model
        - Must have a primary key
        - Must have a __tablename__ attribute
        """
        # Check if it's a SQLAlchemy declarative model
        if not hasattr(model, "__tablename__"):
            raise ValueError(f"Model {model.__name__} must have a __tablename__ attribute")
        
        # Check if it has proper SQLAlchemy metadata
        if not hasattr(model, "__table__"):
            raise ValueError(f"Model {model.__name__} must be a SQLAlchemy declarative model")
        
        # Check if it has a primary key
        if not hasattr(model.__table__, "primary_key") or not model.__table__.primary_key.columns:
            raise ValueError(f"Model {model.__name__} must have a primary key")
        
        # Verify it's a class and not an instance
        if not inspect.isclass(model):
            raise ValueError("model must be a class, not an instance")


# Global registry instance
_global_registry = ModelRegistry()


def get_registry() -> ModelRegistry:
    """Get the global model registry instance."""
    return _global_registry