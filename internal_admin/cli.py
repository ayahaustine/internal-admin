"""
Command-line interface for internal-admin.

Provides management commands for administering the admin framework itself,
independent of any specific project. Commands are registered as package
entry points and available after installation.

Configuration is read exclusively from environment variables. Place a .env
file in the working directory and the command will load it automatically.

Required environment variables:
    DATABASE_URL   SQLAlchemy database URL, e.g. sqlite:///./app.db
    SECRET_KEY     Secret key used for session signing

Usage:
    internal-admin createsuperuser
    internal-admin createsuperuser --username admin --email admin@example.com
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys


def _load_env() -> None:
    """
    Load a .env file from the current working directory if one exists.
    Uses python-dotenv; silently skips if the file is absent.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv(override=False)  # existing env vars always win
    except ImportError:
        pass  # python-dotenv not installed; rely on the shell environment


def cmd_createsuperuser(args: argparse.Namespace) -> int:
    """
    Create an admin superuser in the admin_users table.

    Reads DATABASE_URL and SECRET_KEY from environment variables (or a .env
    file in the current directory). Prompts interactively for any values not
    supplied on the command line.

    Exit codes:
        0  success
        1  user error (validation failure, duplicate username, etc.)
        2  configuration error (missing DATABASE_URL or SECRET_KEY)
    """
    # ------------------------------------------------------------------ config
    _load_env()

    database_url = os.environ.get("DATABASE_URL")
    secret_key = os.environ.get("SECRET_KEY")

    if not database_url:
        print(
            "Error: DATABASE_URL is not set.\n"
            "Add it to your .env file or export it in your shell before running this command.",
            file=sys.stderr,
        )
        return 2

    if not secret_key:
        print(
            "Error: SECRET_KEY is not set.\n"
            "Add it to your .env file or export it in your shell before running this command.",
            file=sys.stderr,
        )
        return 2

    # ---------------------------------------------------------------- imports
    # Deferred so the module can be imported cheaply (e.g. for --help)
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.exc import IntegrityError

        from internal_admin.auth.models import AdminUser, Base
        from internal_admin.auth.security import hash_password, initialize_security
        from internal_admin.config import AdminConfig
        from internal_admin.database.admin_tables import create_admin_tables
    except ImportError as exc:
        print(f"Error: failed to import internal_admin — {exc}", file=sys.stderr)
        return 2

    # ---------------------------------------------------------- security init
    config = AdminConfig(
        database_url=database_url,
        secret_key=secret_key,
        user_model=AdminUser,
    )
    initialize_security(config)

    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    create_admin_tables(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # ------------------------------------------------------- collect username
    username = args.username
    if not username:
        while True:
            username = input("Username: ").strip()
            if username:
                break
            print("Username may not be blank.")

    # ------------------------------------------------------------------ email
    email = args.email
    if email is None:
        raw = input("Email address (leave blank for none): ").strip()
        email = raw or None

    # ---------------------------------------------------------------- password
    password = args.password
    if not password:
        while True:
            password = getpass.getpass("Password: ")
            if len(password) < 8:
                print("Password must be at least 8 characters.")
                continue
            confirm = getpass.getpass("Password (again): ")
            if password != confirm:
                print("Passwords do not match.")
                continue
            break

    # --------------------------------------------------------- validation
    if len(password) < 8:
        print("Error: password must be at least 8 characters.", file=sys.stderr)
        return 1

    try:
        existing = session.query(AdminUser).filter(AdminUser.username == username).first()
        if existing:
            print(f"Error: a user with username '{username}' already exists.", file=sys.stderr)
            return 1

        if email:
            existing_email = session.query(AdminUser).filter(AdminUser.email == email).first()
            if existing_email:
                print(f"Error: a user with email '{email}' already exists.", file=sys.stderr)
                return 1

        user = AdminUser(
            username=username,
            email=email,
            password_hash=hash_password(password),
            is_active=True,
            is_superuser=True,
        )
        session.add(user)
        session.commit()
        print(f"Superuser '{username}' created successfully.")
        return 0

    except IntegrityError as exc:
        session.rollback()
        print(f"Error: database constraint violation — {exc.orig}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        session.rollback()
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="internal-admin",
        description="Management commands for internal-admin.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    subparsers.required = True

    # ---------------------------------------------------- createsuperuser
    su = subparsers.add_parser(
        "createsuperuser",
        help="Create an admin superuser account.",
        description=(
            "Creates a superuser in the admin_users table. "
            "DATABASE_URL and SECRET_KEY are read from environment variables "
            "or a .env file in the current directory."
        ),
    )
    su.add_argument("--username", default=None, help="Username for the new superuser.")
    su.add_argument("--email", default=None, help="Email address (optional).")
    su.add_argument(
        "--password",
        default=None,
        help="Password (not recommended on shared machines — omit to be prompted).",
    )

    return parser


def main() -> None:
    """Entry point registered in pyproject.toml."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "createsuperuser":
        sys.exit(cmd_createsuperuser(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
