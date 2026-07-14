import os

from backend.extensions import db
from backend.repositories.role_repository import RoleRepository
from backend.repositories.user_repository import UserRepository
from backend.services.user_service import UserService


def seed_super_admin():
    user_repository = UserRepository(db)
    role_repository = RoleRepository(db)
    user_service = UserService(
        user_repository=user_repository,
        role_repository=role_repository,
    )

    username = os.getenv("LR_SUPER_ADMIN_USERNAME")
    email = os.getenv("LR_SUPER_ADMIN_EMAIL")
    password = os.getenv("LR_SUPER_ADMIN_PASSWORD")

    if not username or not email or not password:
        raise RuntimeError(
            "Set LR_SUPER_ADMIN_USERNAME, LR_SUPER_ADMIN_EMAIL, and "
            "LR_SUPER_ADMIN_PASSWORD before running the super admin seeder."
        )

    existing_user = user_repository.get_by_username(username)
    if existing_user:
        print("SUPER_ADMIN already exists")
        return

    user = user_service.create_user(
        username=username,
        email=email,
        password=password,
        role_name="SUPER_ADMIN",
    )

    print(f"SUPER_ADMIN created: {user.username}")


if __name__ == "__main__":
    seed_super_admin()
