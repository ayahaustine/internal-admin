# Internal Admin

A reusable, pip-installable administrative framework for FastAPI applications.
Automatically generates a full CRUD interface from your SQLAlchemy models, with
session-based authentication, role-based permissions, and a clean Bootstrap 5 UI
— all rendered server-side with no frontend build tools.

---

## Screenshots

**Dashboard**

![Admin dashboard](dashboard.png)

**Model Management**

![Model list and actions](action.png)

---

## Features

- **Model-driven CRUD** — Automatic create, read, update, and delete for any registered SQLAlchemy model
- **Minimal UI** — Familiar admin interface patterns with good UX
- **SQLAlchemy 2.0** — Built on modern SQLAlchemy with full declarative model support
- **Multi-database** — Works with SQLite (development) and PostgreSQL (production) without code changes
- **Session-based authentication** — Secure HTTP-only cookie sessions with bcrypt password hashing
- **Role-based permissions** — Per-model permission hooks; enforced at the route level, not just the UI
- **Activity logging** — Automatic log of create, update, delete, and login events visible on the dashboard
- **Bootstrap 5 UI** — Clean, responsive server-rendered interface with no JavaScript frameworks
- **Zero build pipeline** — No npm, no webpack, no compilation step

---

## Installation

```bash
pip install internal-admin
```

With PostgreSQL support:

```bash
pip install internal-admin[postgresql]
```

---

## Quick Start

### 1. Define your models

```python
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id      = Column(Integer, primary_key=True)
    name    = Column(String(100))
    email   = Column(String(255), unique=True)
    active  = Column(Boolean, default=True)

    def __str__(self):
        return self.name or f"User {self.id}"
```

### 2. Register models and mount the admin

```python
from fastapi import FastAPI
from internal_admin import AdminSite, AdminConfig, ModelAdmin

class UserAdmin(ModelAdmin):
    list_display   = ["id", "name", "email", "active"]
    search_fields  = ["name", "email"]
    list_filter    = ["active"]

config = AdminConfig(
    database_url="sqlite:///./app.db",
    secret_key="change-me-in-production",
    user_model=User,
)

admin = AdminSite(config)
admin.register(User, UserAdmin)

app = FastAPI()
admin.mount(app)
```

The admin interface is now available at `/admin/`.

### 3. Create a superuser

The command reads `DATABASE_URL` and `SECRET_KEY` from your environment.
The simplest approach is a `.env` file in the project root:

```bash
# .env
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=your-secret-key
```

Then run:

```bash
internal-admin createsuperuser
```

You will be prompted interactively for username, email, and password.
To skip prompts (e.g. in CI), pass them as flags:

```bash
internal-admin createsuperuser \
  --username admin \
  --email admin@example.com \
  --password change-me
```

---

## Configuration

`AdminConfig` accepts the following parameters:

| Parameter              | Required | Default         | Description                             |
|------------------------|----------|-----------------|-----------------------------------------|
| `database_url`         | Yes      | —               | SQLAlchemy database URL                 |
| `secret_key`           | Yes      | —               | Secret key for session signing          |
| `user_model`           | Yes      | —               | SQLAlchemy model used for authentication|
| `session_cookie_name`  | No       | `admin_session` | Name of the HTTP-only session cookie    |
| `login_route`          | No       | `/admin/login`  | Login URL                               |
| `debug`                | No       | `False`         | Enable debug mode                       |

**Environment variables** (alternative to programmatic config):

```bash
export DATABASE_URL="postgresql://user:pass@localhost/mydb"
export SECRET_KEY="a-long-random-secret-key"
```

---

## ModelAdmin Reference

Subclass `ModelAdmin` to control how each model behaves in the admin.

```python
class ArticleAdmin(ModelAdmin):
    # Columns shown on the list page
    list_display = ["id", "title", "author", "published", "created_at"]

    # Fields searched when using the search box
    search_fields = ["title", "body"]

    # Sidebar filter options
    list_filter = ["published"]

    # Default sort order (prefix with "-" to sort descending)
    ordering = ["-created_at"]

    # Fields that cannot be edited
    readonly_fields = ["created_at"]

    # Explicit field order on the create/edit form
    form_fields = ["title", "body", "author", "published"]

    # Fields excluded from all views
    exclude_fields = ["internal_notes"]

    # Rows per page
    page_size = 25
```

### Permission hooks

Override these methods to control access per model:

```python
class ArticleAdmin(ModelAdmin):
    def has_view(self, user) -> bool:
        return user.is_active

    def has_create(self, user) -> bool:
        return user.is_superuser

    def has_update(self, user) -> bool:
        return user.is_superuser

    def has_delete(self, user) -> bool:
        return user.is_superuser
```

### Query and save hooks

```python
class ArticleAdmin(ModelAdmin):
    def get_queryset(self, session):
        # Customize the base query for the list view
        return session.query(self.model).filter(self.model.deleted_at == None)

    def before_save(self, obj):
        # Called before create or update is committed
        obj.slug = slugify(obj.title)

    def after_save(self, obj):
        # Called after commit
        invalidate_cache(obj.id)
```

---

## Running the Demo

A working demo application is included:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Create a superuser before starting the server:

```bash
internal-admin createsuperuser
```

Then start the server:

```bash
python3 demo_web.py
```

Open [http://localhost:8080/admin/](http://localhost:8080/admin/) and log in with the
credentials you just created. No default users are seeded.

---


## Development Setup

```bash
# Clone the repository
git clone https://github.com/ayahaustine/internal-admin.git
cd internal-admin

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Run the test suite
pytest tests/ -v

# Check coverage
pytest tests/ --cov=internal_admin --cov-report=term-missing

# Format code
black internal_admin tests
isort internal_admin tests

# Type checking
mypy internal_admin
```

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines, architecture
constraints, branching workflow, and the pull request process.

All contributors are expected to follow the [Code of Conduct](./CODE_OF_CONDUCT.md).

---

## License

MIT — see [LICENSE](./LICENSE).