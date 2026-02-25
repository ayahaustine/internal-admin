"""
ModelAdmin base class for Internal Admin.

ModelAdmin defines the configuration and behavior for admin 
interface generation for SQLAlchemy models.
"""

from typing import List, Optional, Tuple, Any, Dict, Type
from sqlalchemy.orm import Session

from ..auth.permissions import Permission


class ModelAdmin:
    """
    Base class for model-specific admin configuration.
    
    ModelAdmin defines how a model should be displayed and managed
    in the admin interface. It provides configuration attributes
    and hook methods that can be overridden by subclasses.
    
    This is the primary extension point for customizing admin behavior.
    """
    
    # Display configuration
    list_display: List[str] = []  # Fields to show in list view
    search_fields: List[str] = []  # Fields to search across
    list_filter: List[str] = []   # Fields to filter by
    ordering: List[str] = []      # Default ordering
    readonly_fields: List[str] = []  # Read-only fields in forms
    exclude_fields: List[str] = []   # Fields to exclude from forms
    
    # Form configuration  
    form_fields: Optional[List[str]] = None  # Explicit field order
    
    # Pagination
    page_size: int = 25  # Items per page
    
    def __init__(self, model_class: Type[Any]) -> None:
        """
        Initialize ModelAdmin for a specific model.
        
        Args:
            model_class: SQLAlchemy model class this admin manages
        """
        self.model = model_class
        self._validate_configuration()
    
    def _validate_configuration(self) -> None:
        """Validate ModelAdmin configuration against the model."""
        model_columns = [col.name for col in self.model.__table__.columns]
        
        # Validate list_display fields exist
        for field in self.list_display:
            if field not in model_columns:
                raise ValueError(
                    f"list_display field '{field}' does not exist on model {self.model.__name__}"
                )
        
        # Validate search_fields exist and are text-like
        for field in self.search_fields:
            if field not in model_columns:
                raise ValueError(
                    f"search_fields field '{field}' does not exist on model {self.model.__name__}"
                )
        
        # Validate filter fields exist
        for field in self.list_filter:
            if field not in model_columns:
                raise ValueError(
                    f"list_filter field '{field}' does not exist on model {self.model.__name__}"
                )
    
    def get_list_display(self) -> List[str]:
        """
        Get fields to display in list view.
        
        Returns:
            List of field names to display
        """
        if self.list_display:
            return self.list_display
        
        # Default: show first few columns
        columns = [col.name for col in self.model.__table__.columns]
        return columns[:4]  # Show first 4 columns by default
    
    def get_search_fields(self) -> List[str]:
        """
        Get fields to search across.
        
        Returns:
            List of searchable field names
        """
        return self.search_fields
    
    def get_list_filter(self) -> List[str]:
        """
        Get fields available for filtering.
        
        Returns:
            List of filterable field names
        """
        return self.list_filter
    
    def get_ordering(self) -> List[str]:
        """
        Get default ordering for list view.
        
        Returns:
            List of field names for ordering (prefix with '-' for desc)
        """
        if self.ordering:
            return self.ordering
        
        # Default: order by primary key
        pk_column = self.model.__table__.primary_key.columns.keys()[0]
        return [pk_column]
    
    def get_form_fields(self) -> List[str]:
        """
        Get fields to include in forms.
        
        Returns:
            List of field names for forms
        """
        if self.form_fields is not None:
            return self.form_fields
        
        # Default: all columns except excluded ones
        all_fields = [col.name for col in self.model.__table__.columns]
        return [f for f in all_fields if f not in self.exclude_fields]
    
    def get_readonly_fields(self) -> List[str]:
        """
        Get fields that should be read-only in forms.
        
        Returns:
            List of read-only field names
        """
        return self.readonly_fields
    
    def get_page_size(self) -> int:
        """
        Get page size for list view.
        
        Returns:
            Number of items per page
        """
        return self.page_size
    
    # Permission hooks
    def has_view_permission(self, user: Any) -> bool:
        """
        Check if user can view objects of this model.
        
        Args:
            user: User object to check permissions for
            
        Returns:
            True if user can view objects
        """
        from ..auth.permissions import has_permission
        return has_permission(user, self.model, Permission.VIEW)
    
    def has_create_permission(self, user: Any) -> bool:
        """
        Check if user can create objects of this model.
        
        Args:
            user: User object to check permissions for
            
        Returns:
            True if user can create objects
        """
        from ..auth.permissions import has_permission
        return has_permission(user, self.model, Permission.CREATE)
    
    def has_update_permission(self, user: Any, obj: Optional[Any] = None) -> bool:
        """
        Check if user can update objects of this model.
        
        Args:
            user: User object to check permissions for
            obj: Optional specific object for object-level permissions
            
        Returns:
            True if user can update objects
        """
        from ..auth.permissions import has_permission
        return has_permission(user, self.model, Permission.UPDATE, obj)
    
    def has_delete_permission(self, user: Any, obj: Optional[Any] = None) -> bool:
        """
        Check if user can delete objects of this model.
        
        Args:
            user: User object to check permissions for
            obj: Optional specific object for object-level permissions
            
        Returns:
            True if user can delete objects
        """
        from ..auth.permissions import has_permission
        return has_permission(user, self.model, Permission.DELETE, obj)
    
    # Query hooks
    def get_queryset(self, session: Session) -> Any:
        """
        Get base queryset for this model.
        
        This method can be overridden to customize the base query,
        such as adding filters, eager loading, or access restrictions.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            SQLAlchemy query object
        """
        return session.query(self.model)
    
    def before_save(self, obj: Any, is_create: bool = False) -> None:
        """
        Hook called before saving an object.
        
        Args:
            obj: Model instance being saved
            is_create: True if creating new object, False if updating
        """
        pass
    
    def after_save(self, obj: Any, is_create: bool = False) -> None:
        """
        Hook called after saving an object.
        
        Args:
            obj: Model instance that was saved
            is_create: True if created new object, False if updated
        """
        pass
    
    def before_delete(self, obj: Any) -> None:
        """
        Hook called before deleting an object.
        
        Args:
            obj: Model instance being deleted
        """
        pass
    
    def after_delete(self, obj: Any) -> None:
        """
        Hook called after deleting an object.
        
        Args:
            obj: Model instance that was deleted
        """
        pass