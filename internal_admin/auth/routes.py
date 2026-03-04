"""
Authentication routes for Internal Admin.

Provides login, logout, and session management endpoints.
"""

from typing import Any, Optional
from fastapi import APIRouter, Request, Response, Form, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..config import AdminConfig
from ..database.session import get_session
from .security import get_security_manager
from .models import validate_user_model


def create_auth_router(config: AdminConfig, templates: Jinja2Templates) -> APIRouter:
    """
    Create FastAPI router for authentication endpoints.
    
    Args:
        config: AdminConfig with auth settings
        templates: Jinja2Templates instance for rendering
        
    Returns:
        Configured FastAPI router
    """
    router = APIRouter(tags=["auth"])
    
    # Validate user model
    validate_user_model(config.user_model)
    
    @router.get("/login", response_class=HTMLResponse)
    async def login_page(request: Request) -> HTMLResponse:
        """Display login form."""
        # Check if already logged in
        from ..database.session import get_session
        try:
            db_session = next(get_session())
            user = get_current_user(request, config, db_session)
            if user is not None:
                return RedirectResponse(url="/admin/", status_code=302)
        except:
            pass
            
        context = {
            "request": request,
            "title": "Admin Login",
        }
        return templates.TemplateResponse("auth/login.html", context)
    
    @router.post("/login")
    async def login_submit(
        request: Request,
        response: Response,
        username: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_session)
    ) -> RedirectResponse:
        """Handle login form submission."""
        security = get_security_manager()
        
        # Query user by username or email
        user_query = db.query(config.user_model)
        
        if hasattr(config.user_model, "username"):
            user = user_query.filter(config.user_model.username == username).first()
        elif hasattr(config.user_model, "email"):
            user = user_query.filter(config.user_model.email == username).first()
        else:
            raise ValueError("User model must have either 'username' or 'email' field")
        
        # Verify user and password
        if (
            user is None 
            or not user.is_active 
            or not security.verify_password(password, user.password_hash)
        ):
            # Redirect back to login with error
            return RedirectResponse(
                url="/admin/login?error=invalid_credentials",
                status_code=status.HTTP_302_FOUND
            )
        
        # Update last login if field exists
        if hasattr(user, "last_login"):
            from datetime import datetime
            user.last_login = datetime.utcnow()
            db.commit()
        
        # Create session token
        session_token = security.create_session_token(user.id)
        
        # Set secure cookie
        response = RedirectResponse(url="/admin/", status_code=status.HTTP_302_FOUND)
        response.set_cookie(
            key=config.session_cookie_name,
            value=session_token,
            httponly=True,
            secure=not config.debug,  # Use secure cookies in production
            samesite="lax",
            max_age=86400,  # 24 hours
        )
        
        return response
    
    @router.post("/logout")
    async def logout(request: Request, response: Response) -> RedirectResponse:
        """Handle logout."""
        response = RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
        response.delete_cookie(
            key=config.session_cookie_name,
            httponly=True,
            secure=not config.debug,
            samesite="lax"
        )
        return response
    
    return router


def get_current_user(
    request: Request, 
    config: AdminConfig,
    db: Session = Depends(get_session)
) -> Optional[Any]:
    """
    FastAPI dependency to get current authenticated user.
    
    Args:
        request: FastAPI request object
        config: AdminConfig instance
        db: Database session
        
    Returns:
        User object if authenticated, None otherwise
    """
    # Get session token from cookie
    session_token = request.cookies.get(config.session_cookie_name)
    if not session_token:
        return None
    
    # Verify token and get user ID
    security = get_security_manager()
    user_id = security.verify_session_token(session_token)
    if not user_id:
        return None
    
    # Load user from database
    try:
        user = db.query(config.user_model).filter(
            config.user_model.id == user_id
        ).first()
        
        if user and user.is_active:
            return user
    except Exception:
        # Database error or invalid user model
        pass
    
    return None


def create_auth_dependency(config: AdminConfig):
    """Create authentication dependency for a specific config."""
    def get_current_user_dependency(
        request: Request,
        db: Session = Depends(get_session)
    ) -> Optional[Any]:
        return get_current_user(request, config, db)
    
    def require_auth_dependency(
        user: Optional[Any] = Depends(get_current_user_dependency)
    ) -> Any:
        """Require authentication dependency."""
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        return user
    
    return get_current_user_dependency, require_auth_dependency


# Legacy function for backward compatibility
def require_auth(
    user: Optional[Any] = Depends(get_current_user)
) -> Any:
    """
    FastAPI dependency that requires authentication.
    
    Args:
        user: Current user from get_current_user dependency
        
    Returns:
        Authenticated user object
        
    Raises:
        HTTPException: If user is not authenticated
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user