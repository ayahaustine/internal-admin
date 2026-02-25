"""
Basic tests for Internal Admin functionality.
"""

import pytest
from fastapi.testclient import TestClient

from internal_admin import AdminSite, AdminConfig, ModelAdmin


class TestAdminSite:
    """Test AdminSite functionality."""
    
    def test_admin_site_creation(self, admin_config: AdminConfig):
        """Test AdminSite can be created."""
        site = AdminSite(admin_config)
        assert site.config == admin_config
        assert not site._initialized
    
    def test_model_registration(self, admin_site: AdminSite):
        """Test model registration works."""
        from tests.conftest import TestModel, TestUser
        assert admin_site.is_registered(TestModel)
        assert not admin_site.is_registered(TestUser)
    
    def test_get_registered_models(self, admin_site: AdminSite):
        """Test getting registered models."""
        models = admin_site.get_registered_models()
        assert len(models) == 1
        # Check that TestModel is registered (by class name since import paths may differ)
        model_names = [model.__name__ for model in models.keys()]
        assert "TestModel" in model_names


class TestAdminConfig:
    """Test AdminConfig functionality."""
    
    def test_config_validation(self, test_db: str):
        """Test config validation."""
        from tests.conftest import TestUser
        # Valid config should work
        config = AdminConfig(
            database_url=test_db,
            secret_key="test-key",
            user_model=TestUser
        )
        assert config.database_url == test_db
        assert config.is_sqlite
        assert not config.is_postgresql
    
    def test_invalid_config(self):
        """Test invalid config raises errors."""
        from tests.conftest import TestUser
        with pytest.raises(ValueError, match="database_url is required"):
            AdminConfig(
                database_url="",
                secret_key="test-key",
                user_model=TestUser
            )
        
        with pytest.raises(ValueError, match="secret_key is required"):
            AdminConfig(
                database_url="sqlite:///test.db",
                secret_key="",
                user_model=TestUser
            )


class TestModelAdmin:
    """Test ModelAdmin functionality."""
    
    def test_model_admin_creation(self):
        """Test ModelAdmin can be created."""
        from tests.conftest import TestModel
        admin = ModelAdmin(TestModel)
        assert admin.model == TestModel
    
    def test_list_display(self):
        """Test list_display configuration."""
        from tests.conftest import TestModel
        admin = ModelAdmin(TestModel)
        
        # Should return default columns if not configured
        display_fields = admin.get_list_display()
        assert "id" in display_fields
        assert "name" in display_fields
    
    def test_search_fields(self):
        """Test search_fields configuration."""
        from tests.conftest import TestModel
        admin = ModelAdmin(TestModel)
        admin.search_fields = ["name"]
        
        search_fields = admin.get_search_fields()
        assert search_fields == ["name"]


class TestAdminRoutes:
    """Test admin route functionality."""
    
    def test_dashboard_requires_auth(self, client: TestClient):
        """Test dashboard requires authentication."""
        response = client.get("/admin/")
        assert response.status_code == 401
    
    def test_login_page(self, client: TestClient):
        """Test login page is accessible."""
        response = client.get("/admin/login")
        assert response.status_code == 200
        assert "login" in response.text.lower()
    
    def test_model_list_requires_auth(self, client: TestClient):
        """Test model list requires authentication."""
        response = client.get("/admin/testmodel/")
        assert response.status_code == 401


class TestAuthentication:
    """Test authentication functionality."""
    
    def test_successful_login(self, client: TestClient, test_user):
        """Test successful login."""
        response = client.post("/admin/login", data={
            "username": test_user.username,
            "password": "testpass123"
        })
        assert response.status_code == 302  # Redirect after login
    
    def test_invalid_login(self, client: TestClient):
        """Test invalid login credentials."""
        response = client.post("/admin/login", data={
            "username": "nonexistent",
            "password": "wrongpass"
        })
        assert response.status_code == 302  # Redirect to login with error
        assert "error=invalid_credentials" in response.headers["location"]
    
    def test_authenticated_dashboard_access(self, authenticated_client: TestClient):
        """Test authenticated users can access dashboard."""
        response = authenticated_client.get("/admin/")
        assert response.status_code == 200
        assert "dashboard" in response.text.lower()


class TestCRUDOperations:
    """Test CRUD operations via admin interface."""
    
    def test_model_list_view(self, authenticated_client: TestClient, test_objects):
        """Test model list view."""
        response = authenticated_client.get("/admin/testmodel/")
        assert response.status_code == 200
        assert "Test 1" in response.text
        assert "Test 2" in response.text
    
    def test_create_form_view(self, authenticated_client: TestClient):
        """Test create form view."""
        response = authenticated_client.get("/admin/testmodel/create/")
        assert response.status_code == 200
        assert "form" in response.text.lower()
        assert "name" in response.text.lower()
    
    def test_create_object(self, authenticated_client: TestClient):
        """Test creating new object."""
        response = authenticated_client.post("/admin/testmodel/create/", data={
            "name": "New Test Object",
            "description": "Created via test",
            "is_active": True
        })
        assert response.status_code == 302  # Redirect after create
    
    def test_edit_form_view(self, authenticated_client: TestClient, test_objects):
        """Test edit form view."""
        response = authenticated_client.get(f"/admin/testmodel/{test_objects[0].id}/")
        assert response.status_code == 200
        assert test_objects[0].name in response.text
    
    def test_delete_confirmation(self, authenticated_client: TestClient, test_objects):
        """Test delete confirmation page."""
        response = authenticated_client.get(f"/admin/testmodel/{test_objects[0].id}/delete/")
        assert response.status_code == 200
        assert "delete" in response.text.lower()
        assert test_objects[0].name in response.text


class TestSearchAndFiltering:
    """Test search and filtering functionality."""
    
    def test_search(self, authenticated_client: TestClient, test_objects):
        """Test search functionality."""
        response = authenticated_client.get("/admin/testmodel/?search=Test 1")
        assert response.status_code == 200
        assert "Test 1" in response.text
    
    def test_filter(self, authenticated_client: TestClient, test_objects):
        """Test filtering functionality."""
        response = authenticated_client.get("/admin/testmodel/?is_active=true")
        assert response.status_code == 200
        # Should show active objects but not inactive ones


class TestPermissions:
    """Test permission system."""
    
    def test_superuser_permissions(self, authenticated_client: TestClient):
        """Test superuser has all permissions."""
        # Should be able to access model list
        response = authenticated_client.get("/admin/testmodel/")
        assert response.status_code == 200
        
        # Should be able to access create form
        response = authenticated_client.get("/admin/testmodel/create/")
        assert response.status_code == 200