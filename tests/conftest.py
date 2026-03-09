"""
Test configuration and fixtures for Internal Admin tests.
"""

import os
import tempfile
from typing import Generator, Any
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

from internal_admin import AdminSite, AdminConfig, ModelAdmin
from internal_admin.auth.models import AdminUser
from internal_admin.auth.security import hash_password

# Test database setup
Base = declarative_base()


class TestUser(Base):
    """Test user model for authentication."""
    __tablename__ = "test_users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    password_hash = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    @property
    def display_name(self) -> str:
        return self.username or f"User {self.id}"


class TestModel(Base):
    """Simple test model for admin testing."""
    __tablename__ = "test_models"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(String(255))
    is_active = Column(Boolean, default=True)


class TestCategory(Base):
    """Related model for foreign key tests."""
    __tablename__ = "test_categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    products = relationship("TestProduct", back_populates="category")

    def __str__(self) -> str:
        return self.name


class TestProduct(Base):
    """Model containing a foreign key for admin tests."""
    __tablename__ = "test_products"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    category_id = Column(Integer, ForeignKey("test_categories.id"), nullable=False)
    is_active = Column(Boolean, default=True)

    category = relationship("TestCategory", back_populates="products")


class TestModelAdmin(ModelAdmin):
    """Test ModelAdmin configuration."""
    list_display = ["id", "name", "is_active"]
    search_fields = ["name", "description"]
    list_filter = ["is_active"]


class TestCategoryAdmin(ModelAdmin):
    """Admin configuration for category model."""
    list_display = ["id", "name"]
    search_fields = ["name"]


class TestProductAdmin(ModelAdmin):
    """Admin configuration for product model."""
    list_display = ["id", "name", "category_id", "is_active"]
    search_fields = ["name"]
    list_filter = ["category_id", "is_active"]


@pytest.fixture(scope="session")
def test_db() -> Generator[str, None, None]:
    """Create a temporary test database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    db_url = f"sqlite:///{db_path}"
    
    # Create engine and tables
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    
    yield db_url
    
    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def admin_config(test_db: str) -> AdminConfig:
    """Create AdminConfig for testing."""
    return AdminConfig(
        database_url=test_db,
        secret_key="test-secret-key-for-testing-only",
        user_model=TestUser,  # Use TestUser, not TestModel
        debug=True,
    )


@pytest.fixture
def admin_site(admin_config: AdminConfig) -> AdminSite:
    """Create AdminSite for testing."""
    # Clear the registry before each test
    from internal_admin.registry import _global_registry
    _global_registry._registry.clear()
    
    # Create fresh AdminSite after clearing registry
    site = AdminSite(admin_config)
    site.register(TestModel, TestModelAdmin)
    site.register(TestCategory, TestCategoryAdmin)
    site.register(TestProduct, TestProductAdmin)
    return site


@pytest.fixture
def app(admin_site: AdminSite) -> FastAPI:
    """Create FastAPI app with admin mounted."""
    app = FastAPI(title="Test Admin App")
    admin_site.mount(app)
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def db_session(admin_config: AdminConfig) -> Generator[Session, None, None]:
    """Create database session for testing."""
    from internal_admin.database.engine import initialize_engine
    from internal_admin.database.session import initialize_session_manager, get_session_manager
    
    # Initialize database
    initialize_engine(admin_config)
    initialize_session_manager()
    
    session_manager = get_session_manager()
    
    with session_manager.get_session() as session:
        yield session


@pytest.fixture
def test_user(db_session: Session) -> TestUser:
    """Create a test user."""
    user = TestUser(
        username="testuser",
        password_hash=hash_password("testpass123"),
        is_active=True,
        is_superuser=True
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_objects(db_session: Session) -> list[TestModel]:
    """Create test model objects."""
    objects = [
        TestModel(name="Test 1", description="First test object", is_active=True),
        TestModel(name="Test 2", description="Second test object", is_active=False),
        TestModel(name="Test 3", description="Third test object", is_active=True),
    ]
    
    for obj in objects:
        db_session.add(obj)
    
    db_session.commit()
    return objects


@pytest.fixture
def fk_objects(db_session: Session) -> dict[str, Any]:
    """Create related objects for foreign key tests."""
    categories = [
        TestCategory(name="Hardware"),
        TestCategory(name="Software"),
    ]
    db_session.add_all(categories)
    db_session.flush()

    products = [
        TestProduct(name="Keyboard", category_id=categories[0].id, is_active=True),
        TestProduct(name="IDE License", category_id=categories[1].id, is_active=True),
    ]
    db_session.add_all(products)
    db_session.commit()

    return {
        "categories": categories,
        "products": products,
    }


@pytest.fixture
def authenticated_client(client: TestClient, test_user: TestUser) -> TestClient:
    """Create authenticated test client."""
    # Login
    response = client.post("/admin/login", data={
        "username": test_user.username,
        "password": "testpass123"
    })
    
    assert response.status_code == 302  # Redirect after login
    return client