# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Releases are automated via [python-semantic-release](https://python-semantic-release.readthedocs.io/)
using [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

---

## [Unreleased]

---

## [0.1.0] - 2026-03-04

### Added

- `AdminSite`, `ModelAdmin`, and `AdminConfig` as the stable public API
- Automatic CRUD route generation per registered SQLAlchemy model
  (`GET`/`POST` list, create, edit, delete with confirmation)
- Model registry with validation (primary key presence, declarative model check,
  duplicate registration guard)
- Query engine with search, boolean/foreign-key filters, configurable ordering,
  and pagination — all in a single pipeline
- Form engine: SQLAlchemy column introspection mapping types to HTML widgets
  (text, textarea, checkbox, datetime-local, number, select)
- Session-based authentication with HTTP-only cookies and bcrypt password hashing
- Built-in `AdminUser` model (`admin_users` table) with `username`, `email`,
  `is_active`, `is_superuser`, `created_at`, `last_login`
- `internal-admin createsuperuser` CLI command — reads `DATABASE_URL` and
  `SECRET_KEY` from environment or `.env` file; no default users are ever seeded
- Activity logging: `ActivityLog` model records create, update, delete, and login
  events with user, IP, user-agent, and timestamp
- Dashboard showing registered model counts and the 10 most recent activity
  log entries
- Bootstrap 5 server-rendered UI (sidebar, navbar, list, form, confirm-delete
  templates) — no JavaScript frameworks, no build pipeline
- Standalone login page (no sidebar/navbar) with client-side field validation,
  show/hide password toggle, and loading state
- Logout confirmation modal
- User profile modal accessible from the navbar dropdown (display name, email,
  role badge, member-since, last-login)
- `python-dotenv` integration: `.env` file loaded automatically in both the CLI
  and demo server
- `demo_web.py` demo server registering `DemoCategory`, `DemoProduct`, and
  `AdminUser` in the admin panel
- `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md`

### Security

- Passwords are hashed with bcrypt via passlib; plaintext passwords are never
  stored or logged
- Session cookies are HTTP-only
- `password_hash` excluded from all admin forms by default when `AdminUser` is
  registered

---

[Unreleased]: https://github.com/ayahaustine/internal-admin/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ayahaustine/internal-admin/releases/tag/v0.1.0