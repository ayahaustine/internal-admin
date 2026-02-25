#!/usr/bin/env python3
"""
Create superuser script for Internal Admin Example.

This script creates a superuser account for testing the admin interface.
"""

import sys
import getpass
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Import from the example
from example import User, Base
from internal_admin.auth.security import hash_password, initialize_security
from internal_admin.config import AdminConfig


def create_superuser():
    """Create a superuser account."""
    
    # Initialize security manager with proper config
    config = AdminConfig(
        database_url="sqlite:///./example.db",
        secret_key="demo-secret-key-for-superuser-creation",
        user_model=User,
        debug=True
    )
    initialize_security(config)
    
    # Database setup
    engine = create_engine(config.database_url)
    
    # Create tables if they don't exist
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("🔐 Create Superuser Account")
        print("=" * 40)
        
        # Get user input
        username = input("Username: ").strip()
        if not username:
            print("❌ Username cannot be empty")
            return False
        
        email = input("Email (optional): ").strip() or None
        first_name = input("First Name (optional): ").strip() or None
        last_name = input("Last Name (optional): ").strip() or None
        
        # Get password securely
        password = getpass.getpass("Password: ")
        password_confirm = getpass.getpass("Confirm Password: ")
        
        if password != password_confirm:
            print("❌ Passwords don't match")
            return False
        
        if len(password) < 4:
            print("❌ Password must be at least 4 characters long")
            return False
            
        if len(password) > 50:
            print("❌ Password must be less than 50 characters long")
            return False
        
        # Check if username already exists
        existing_user = session.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"❌ User '{username}' already exists")
            return False
        
        # Create user
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=hash_password(password),
            is_active=True,
            is_superuser=True
        )
        
        session.add(user)
        session.commit()
        
        print(f"✅ Superuser '{username}' created successfully!")
        print(f"📊 You can now log in to the admin at: http://localhost:8000/admin/")
        print()
        print("To start the development server, run:")
        print("python example.py")
        
        return True
        
    except IntegrityError as e:
        session.rollback()
        print(f"❌ Database error: {e}")
        return False
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
        return False
    except Exception as e:
        session.rollback()
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        session.close()


if __name__ == "__main__":
    success = create_superuser()
    sys.exit(0 if success else 1)