# Internal Admin

A reusable, installable administrative framework for FastAPI applications.

## Features

- **Model-driven CRUD interface** - Automatic admin interface generation from SQLAlchemy models
- **Django-style admin UX** - Familiar administrative interface patterns  
- **SQLAlchemy 2.0 integration** - Full support for modern SQLAlchemy features
- **Multi-database support** - SQLite (default) and PostgreSQL
- **Session-based authentication** - Secure, HTTP-only cookie authentication
- **Role-based permissions** - Extensible permission system
- **Bootstrap UI** - Clean, responsive server-rendered interface
- **Zero build tools** - No frontend compilation required

## Quick Start

### Installation

```bash
pip install internal-admin
```

With PostgreSQL support:
```bash
pip install internal-admin[postgresql]
```

### Basic Usage

```python
from fastapi import FastAPI
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from internal_admin import AdminSite, AdminConfig, ModelAdmin

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(255))

class UserAdmin(ModelAdmin):
    list_display = ["id", "name", "email"]
    search_fields = ["name", "email"]

# Configure admin
config = AdminConfig(
    database_url="sqlite:///./app.db",
    secret_key="your-secret-key-here",
    user_model=User
)

# Create admin site
admin = AdminSite(config)
admin.register(User, UserAdmin)

# Mount to FastAPI app
app = FastAPI()
admin.mount(app)
```

### Configuration

Set environment variables:

```bash
export DATABASE_URL="sqlite:///./app.db"
export SECRET_KEY="your-secret-key-here"
```

Or configure programmatically:

```python
from internal_admin import AdminConfig

config = AdminConfig(
    database_url="postgresql://user:pass@localhost/db",
    secret_key="your-secret-key",
    user_model=YourUserModel,
    session_cookie_name="admin_session",
    debug=True
)
```

## Architecture

Internal Admin follows these principles:

- **Model-driven** - Admin behavior derives from SQLAlchemy models
- **Registry-based** - Models must be explicitly registered  
- **Separation of concerns** - UI, routing, query logic isolated
- **Stable public API** - Minimal exposed interfaces
- **Extensible via hooks** - Controlled override points
- **DB-agnostic** - Works with SQLite and PostgreSQL


## Development

### Setup

```bash
# Clone repository
git clone https://github.com/ayahaustine/internal-admin.git
cd internal-admin

# Setup development environment with uv
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
black internal_admin tests
isort internal_admin tests

# Type checking
mypy internal_admin
```

## License

MIT License - see [LICENSE](./LICENSE) file.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines.