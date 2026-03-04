# Contributing to internal-admin

Thank you for your interest in contributing. This document explains how to work
with this codebase, what standards are expected, and how contributions are
reviewed and merged.

Please read it fully before opening a pull request.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Development Setup](#development-setup)
- [Branching and Workflow](#branching-and-workflow)
- [Code Standards](#code-standards)
- [Architecture Constraints](#architecture-constraints)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Versioning and Changelog](#versioning-and-changelog)
- [What Not to Do](#what-not-to-do)

---

## Project Overview

internal-admin is a reusable, pip-installable administrative framework for
FastAPI applications. It provides model-driven CRUD interfaces, session-based
authentication, and a role-based permission system — all rendered server-side
with Jinja2 and Bootstrap 5.

The public API is intentionally minimal:

- `AdminSite`
- `ModelAdmin`
- `AdminConfig`

Everything else is internal and may change between minor versions. Keep that
boundary in mind when contributing.

---

## Development Setup

**Requirements:** Python 3.10+, pip, git.

```bash
# Clone the repository
git clone https://github.com/ayahaustine/internal-admin.git
cd internal-admin

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

To run the demo server:

```bash
python3 demo_web.py
# Admin interface: http://localhost:8080/admin/
# Login: admin / password123
```

To run the test suite:

```bash
pytest tests/ -v
```

---

## Branching and Workflow

- `main` is the stable branch. Do not commit directly to it.
- Create a branch for every change: `feature/your-feature` or `fix/your-fix`.
- Keep branches focused. One logical change per pull request.
- Rebase on `main` before opening a PR to keep history clean.

```bash
git checkout -b feature/my-feature
# make changes
git push origin feature/my-feature
# open a pull request
```

---

## Code Standards

**Language:** Python 3.10+. Use type annotations throughout.

**Style:** Follow PEP 8. Use a formatter (black or ruff) before pushing.

**Imports:** Absolute imports within the package. Internal modules should
import from their own layer only — do not reach across boundaries (e.g., admin
modules must not import from auth internals and vice versa).

**Naming:** Be explicit. Prefer `model_admin_class` over `mac`.
Avoid abbreviations unless they are universally understood.

**Comments:** Comment the *why*, not the *what*. If a block requires
a comment to be understood, that is a signal to simplify the code first.

**Error handling:** Raise specific, descriptive exceptions. Never silently
swallow exceptions unless the failure is genuinely inconsequential and the
decision is documented.

**Templates:** Jinja2 + Bootstrap 5 only. No JavaScript frameworks. No
business logic in templates — pass everything needed from the route handler.

---

## Architecture Constraints

These are hard constraints, not preferences. Pull requests that violate them
will not be merged.

**Query pipeline.** All list-page query logic must pass through the query
engine pipeline: `base_query → filters → search → ordering → pagination`.
Route handlers must not manually modify queries outside this pipeline.

**No unbounded queries.** Pagination is mandatory on every list endpoint.
Never query an entire table without a limit.

**No N+1 queries.** Use `selectinload` for related objects. Do not lazy-load
inside loops.

**DB-agnostic.** The codebase must work with both SQLite and PostgreSQL.
No database-specific SQL, functions, or assumptions are permitted.

**Public API stability.** Do not add parameters, change signatures, or alter
behavior of `AdminSite`, `ModelAdmin`, or `AdminConfig` without a major
version bump and a migration note in the changelog.

**Separation of concerns.** Admin logic must not reference business logic.
Routing, query building, form handling, and authentication are separate layers
and must remain so.

**No new heavy dependencies.** If a change requires a new dependency, justify
it in the PR description. Prefer the standard library or libraries already in
use.

---

## Testing Requirements

All new logic must be covered by tests. This is not optional.

**Critical areas that require tests for any change:**

- Registry validation
- Query engine pipeline (filters, search, ordering, pagination)
- Form validation and type casting
- Permission enforcement (route level and query level)

**To add a test:**

1. Place it in `tests/`.
2. Follow the naming convention: `test_<module>.py`.
3. Use the fixtures defined in `tests/conftest.py`.
4. Tests must pass against SQLite. PostgreSQL integration tests are encouraged
   for database-layer changes.

**Coverage target:** 85% or higher. Do not submit a PR that reduces overall
coverage without a clear justification.

```bash
pytest tests/ --cov=internal_admin --cov-report=term-missing
```

---

## Pull Request Process

1. **Open an issue first** for non-trivial changes. Discuss the approach before
   writing code.
2. **Write tests** for everything you add or change.
3. **Update the changelog** under `[Unreleased]` in `CHANGELOG.md`.
4. **Fill out the PR description** with:
   - What the change does
   - Why it is needed
   - What tests cover it
   - Whether it affects the public API
5. **Keep the diff focused.** Do not include unrelated formatting changes or
   refactors in the same PR.
6. **Address review comments** directly. If you disagree with feedback, explain
   your reasoning — do not silently ignore it.

A PR requires at least one approving review before it can be merged.
Direct merges to `main` are not permitted.

---

## Versioning and Changelog

This project uses [Semantic Versioning](https://semver.org).

| Change type         | Version bump |
|---------------------|--------------|
| Bug fix             | Patch (0.0.x) |
| New feature         | Minor (0.x.0) |
| Breaking change     | Major (x.0.0) |

Every pull request that changes behavior must include a changelog entry in
`CHANGELOG.md` under the `[Unreleased]` section. Use the appropriate
category: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, or `Security`.

Breaking changes additionally require:

- A major version increment
- A migration note describing what callers need to change

---

## What Not to Do

The following will cause a PR to be declined:

- Adding logic that bypasses the query engine
- Introducing unbounded queries or disabling pagination
- Coupling admin logic to application-specific business logic
- Expanding the public API without a version bump
- Adding magic behavior (auto-discovery, implicit side effects, monkey-patching)
- Submitting without tests
- Committing directly to `main`
- Adding frontend build tooling, JS frameworks, or CSS preprocessors
- Storing or logging plaintext passwords or session tokens

If you are unsure whether a change is appropriate, open an issue and ask before
writing code.

---

## Questions

Open a GitHub issue labeled `question` for anything not covered here.
