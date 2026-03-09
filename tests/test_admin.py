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
        model_names = [model.__name__ for model in models.keys()]
        assert "TestModel" in model_names


class TestAdminConfig:
    """Test AdminConfig functionality."""

    def test_config_validation(self, test_db: str):
        """Test config validation."""
        from tests.conftest import TestUser
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
        assert response.status_code == 302

    def test_invalid_login(self, client: TestClient):
        """Test invalid login credentials."""
        response = client.post("/admin/login", data={
            "username": "nonexistent",
            "password": "wrongpass"
        })
        assert response.status_code == 302
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
        assert response.status_code == 302

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


class TestPermissions:
    """Test permission system."""

    def test_superuser_permissions(self, authenticated_client: TestClient):
        """Test superuser has all permissions."""
        response = authenticated_client.get("/admin/testmodel/")
        assert response.status_code == 200

        response = authenticated_client.get("/admin/testmodel/create/")
        assert response.status_code == 200


class TestForeignKeys:
    """Test foreign key functionality in forms and filters."""

    def test_fk_field_renders_select_choices(self, authenticated_client: TestClient, fk_objects):
        """Create form should render related model choices for FK fields."""
        response = authenticated_client.get("/admin/testproduct/create/")
        assert response.status_code == 200
        assert "category_id" in response.text
        assert "Hardware" in response.text
        assert "Software" in response.text

    def test_fk_create_submission_persists_relation(self, authenticated_client: TestClient, db_session, fk_objects):
        """Submitting FK value should be validated and persisted correctly."""
        from tests.conftest import TestProduct

        hardware_id = fk_objects["categories"][0].id
        response = authenticated_client.post("/admin/testproduct/create/", data={
            "name": "Mouse",
            "category_id": str(hardware_id),
            "is_active": "true",
        })

        assert response.status_code == 302

        created = db_session.query(TestProduct).filter(TestProduct.name == "Mouse").first()
        assert created is not None
        assert created.category_id == hardware_id

    def test_fk_filter_applies_correctly(self, authenticated_client: TestClient, fk_objects):
        """FK list filter should match rows by related ID."""
        software_id = fk_objects["categories"][1].id
        response = authenticated_client.get(f"/admin/testproduct/?category_id={software_id}")

        assert response.status_code == 200
        assert "IDE License" in response.text
        assert "Keyboard" not in response.text
