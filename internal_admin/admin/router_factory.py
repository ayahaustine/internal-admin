"""
Router factory for Internal Admin.

Generates FastAPI routes for CRUD operations on registered models.
"""

from typing import Any, Dict, Optional, Type
from fastapi import APIRouter, Request, Response, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..config import AdminConfig
from ..database.session import get_session
from ..auth.routes import get_current_user, require_auth
from ..auth.permissions import Permission
from .model_admin import ModelAdmin
from .query_engine import QueryEngine
from .form_engine import FormEngine
from .filters import FilterManager


class AdminRouterFactory:
    """
    Factory for creating FastAPI routers for admin models.
    
    Generates standardized CRUD routes for each registered model,
    handling permissions, form processing, and template rendering.
    """
    
    def __init__(self, config: AdminConfig, templates: Jinja2Templates) -> None:
        """
        Initialize AdminRouterFactory.
        
        Args:
            config: AdminConfig instance
            templates: Jinja2Templates for rendering
        """
        self.config = config
        self.templates = templates
    
    def create_model_router(
        self,
        model_class: Type[Any],
        model_admin: ModelAdmin
    ) -> APIRouter:
        """
        Create FastAPI router for a model.
        
        Args:
            model_class: SQLAlchemy model class
            model_admin: ModelAdmin configuration
            
        Returns:
            FastAPI router with CRUD endpoints
        """
        model_name = model_class.__name__.lower()
        router = APIRouter(prefix=f"/admin/{model_name}", tags=[f"admin-{model_name}"])
        
        # Initialize engines
        query_engine = QueryEngine(model_admin)
        form_engine = FormEngine(model_admin)
        filter_manager = FilterManager(model_admin)
        
        @router.get("/", response_class=HTMLResponse, name=f"{model_name}_list")
        async def list_view(
            request: Request,
            page: int = 1,
            search: Optional[str] = None,
            user: Any = Depends(require_auth),
            db: Session = Depends(get_session)
        ) -> HTMLResponse:
            """List view for model objects."""
            # Check permissions
            if not model_admin.has_view_permission(user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied"
                )
            
            # Extract filters from query params
            filters = {}
            for key, value in request.query_params.items():
                if key not in ('page', 'search') and value:
                    filters[key] = value
            
            # Execute query
            result = query_engine.execute_query(
                session=db,
                search_query=search,
                filters=filters,
                page=page
            )
            
            # Get filter context
            filter_context = filter_manager.get_filter_context(db, filters)
            
            context = {
                "request": request,
                "model_name": model_class.__name__,
                "model_name_plural": f"{model_class.__name__}s",
                "objects": result.items,
                "pagination": {
                    "page": result.page,
                    "total_pages": result.total_pages,
                    "total_count": result.total_count,
                    "has_previous": result.has_previous,
                    "has_next": result.has_next,
                    "previous_page": result.previous_page,
                    "next_page": result.next_page,
                },
                "list_display": model_admin.get_list_display(),
                "search_query": search or "",
                "filters": filter_context,
                "current_filters": filters,
                "can_create": model_admin.has_create_permission(user),
            }
            
            return self.templates.TemplateResponse("admin/list.html", context)
        
        @router.get("/create/", response_class=HTMLResponse, name=f"{model_name}_create")
        async def create_form(
            request: Request,
            user: Any = Depends(require_auth),
            db: Session = Depends(get_session)
        ) -> HTMLResponse:
            """Create form for new model object."""
            # Check permissions
            if not model_admin.has_create_permission(user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied"
                )
            
            # Generate form fields
            form_fields = form_engine.generate_form_fields(db)
            
            context = {
                "request": request,
                "model_name": model_class.__name__,
                "form_fields": form_fields,
                "is_create": True,
                "title": f"Create {model_class.__name__}",
            }
            
            return self.templates.TemplateResponse("admin/form.html", context)
        
        @router.post("/create/", name=f"{model_name}_create_submit")
        async def create_submit(
            request: Request,
            user: Any = Depends(require_auth),
            db: Session = Depends(get_session)
        ) -> RedirectResponse:
            """Handle create form submission."""
            # Check permissions
            if not model_admin.has_create_permission(user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied"
                )
            
            # Get form data
            form_data = await request.form()
            form_dict = dict(form_data)
            
            try:
                # Validate form data
                validated_data = form_engine.validate_form_data(form_dict)
                
                # Create new instance
                instance = model_class()
                
                # Call before_save hook
                model_admin.before_save(instance, is_create=True)
                
                # Populate instance
                form_engine.populate_instance(instance, validated_data)
                
                # Save to database
                db.add(instance)
                db.commit()
                
                # Call after_save hook
                model_admin.after_save(instance, is_create=True)
                
                # Redirect to list view
                return RedirectResponse(
                    url=f"/admin/{model_name}/",
                    status_code=status.HTTP_302_FOUND
                )
            
            except Exception as e:
                # Handle validation or database errors
                db.rollback()
                
                # Re-render form with error
                form_fields = form_engine.generate_form_fields(db)
                
                context = {
                    "request": request,
                    "model_name": model_class.__name__,
                    "form_fields": form_fields,
                    "is_create": True,
                    "title": f"Create {model_class.__name__}",
                    "error": str(e),
                    "form_data": form_dict,
                }
                
                return self.templates.TemplateResponse("admin/form.html", context)
        
        @router.get("/{item_id}/", response_class=HTMLResponse, name=f"{model_name}_edit")
        async def edit_form(
            request: Request,
            item_id: int,
            user: Any = Depends(require_auth),
            db: Session = Depends(get_session)
        ) -> HTMLResponse:
            """Edit form for existing model object."""
            # Get object
            obj = db.query(model_class).filter(
                model_class.id == item_id
            ).first()
            
            if not obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Object not found"
                )
            
            # Check permissions
            if not model_admin.has_update_permission(user, obj):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied"
                )
            
            # Generate form fields with current values
            form_fields = form_engine.generate_form_fields(db, instance=obj)
            
            context = {
                "request": request,
                "model_name": model_class.__name__,
                "form_fields": form_fields,
                "is_create": False,
                "title": f"Edit {model_class.__name__}",
                "object": obj,
                "object_id": item_id,
            }
            
            return self.templates.TemplateResponse("admin/form.html", context)
        
        @router.post("/{item_id}/", name=f"{model_name}_edit_submit")
        async def edit_submit(
            request: Request,
            item_id: int,
            user: Any = Depends(require_auth),
            db: Session = Depends(get_session)
        ) -> RedirectResponse:
            """Handle edit form submission."""
            # Get object
            obj = db.query(model_class).filter(
                model_class.id == item_id
            ).first()
            
            if not obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Object not found"
                )
            
            # Check permissions
            if not model_admin.has_update_permission(user, obj):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied"
                )
            
            # Get form data
            form_data = await request.form()
            form_dict = dict(form_data)
            
            try:
                # Validate form data
                validated_data = form_engine.validate_form_data(form_dict)
                
                # Call before_save hook
                model_admin.before_save(obj, is_create=False)
                
                # Update instance
                form_engine.populate_instance(obj, validated_data)
                
                # Save to database
                db.commit()
                
                # Call after_save hook
                model_admin.after_save(obj, is_create=False)
                
                # Redirect to list view
                return RedirectResponse(
                    url=f"/admin/{model_name}/",
                    status_code=status.HTTP_302_FOUND
                )
            
            except Exception as e:
                # Handle validation or database errors
                db.rollback()
                
                # Re-render form with error
                form_fields = form_engine.generate_form_fields(db, instance=obj)
                
                context = {
                    "request": request,
                    "model_name": model_class.__name__,
                    "form_fields": form_fields,
                    "is_create": False,
                    "title": f"Edit {model_class.__name__}",
                    "object": obj,
                    "object_id": item_id,
                    "error": str(e),
                    "form_data": form_dict,
                }
                
                return self.templates.TemplateResponse("admin/form.html", context)
        
        @router.get("/{item_id}/delete/", response_class=HTMLResponse, name=f"{model_name}_delete")
        async def delete_confirmation(
            request: Request,
            item_id: int,
            user: Any = Depends(require_auth),
            db: Session = Depends(get_session)
        ) -> HTMLResponse:
            """Delete confirmation page."""
            # Get object
            obj = db.query(model_class).filter(
                model_class.id == item_id
            ).first()
            
            if not obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Object not found"
                )
            
            # Check permissions
            if not model_admin.has_delete_permission(user, obj):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied"
                )
            
            context = {
                "request": request,
                "model_name": model_class.__name__,
                "object": obj,
                "object_id": item_id,
            }
            
            return self.templates.TemplateResponse("admin/confirm_delete.html", context)
        
        @router.post("/{item_id}/delete/", name=f"{model_name}_delete_submit")
        async def delete_submit(
            request: Request,
            item_id: int,
            user: Any = Depends(require_auth),
            db: Session = Depends(get_session)
        ) -> RedirectResponse:
            """Handle delete confirmation."""
            # Get object
            obj = db.query(model_class).filter(
                model_class.id == item_id
            ).first()
            
            if not obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Object not found"
                )
            
            # Check permissions
            if not model_admin.has_delete_permission(user, obj):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied"
                )
            
            try:
                # Call before_delete hook
                model_admin.before_delete(obj)
                
                # Delete object
                db.delete(obj)
                db.commit()
                
                # Call after_delete hook
                model_admin.after_delete(obj)
                
                # Redirect to list view
                return RedirectResponse(
                    url=f"/admin/{model_name}/",
                    status_code=status.HTTP_302_FOUND
                )
            
            except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error deleting object: {str(e)}"
                )
        
        return router