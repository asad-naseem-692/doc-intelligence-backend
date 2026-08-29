import os
import sys
import argparse

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User


def seed_admin(name: str, email: str, password: str):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"User with email '{email}' already exists. Current role: {existing.role}")
            if existing.role != "admin":
                existing.role = "admin"
                db.commit()
                print(f"Updated existing user '{email}' to admin role.")
            return

        admin_user = User(
            name=name,
            email=email,
            hashed_password=get_password_hash(password),
            role="admin",
            is_active=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"Admin user '{email}' (ID: {admin_user.id}) created successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed an admin user")
    parser.add_argument("--name", default="Administrator", help="Admin user name")
    parser.add_argument("--email", default="admin@example.com", help="Admin email")
    parser.add_argument("--password", default="Admin123!", help="Admin password")
    
    args = parser.parse_args()
    seed_admin(args.name, args.email, args.password)
