from shared.security.password import hash_password
from backend.services.windows_account_service import WindowsAccountService


class UserService:

    def __init__(self, user_repository, role_repository):
        self.user_repository = user_repository
        self.role_repository = role_repository

    def create_user(
        self,
        username,
        email,
        password,
        role_name,
        windows_username=None,
        windows_password=None,
        windows_domain=None,
        windows_account_enabled=False,
        windows_create_account=False,
    ):
        if self.user_repository.exists_by_username(username):
            raise ValueError("Username already exists")

        if self.user_repository.exists_by_email(email):
            raise ValueError("Email already exists")

        role = self.role_repository.get_by_name(role_name)
        if not role:
            raise ValueError("Role not found")

        windows_updates, windows_error = WindowsAccountService.build_updates(
            {
                "windows_username": windows_username,
                "windows_password": windows_password,
                "windows_domain": windows_domain,
                "windows_account_enabled": windows_account_enabled,
            },
            default_username=username,
            default_password=password,
            create_local_account=windows_create_account,
        )
        if windows_error:
            raise ValueError(windows_error)

        user = {
            "username": username,
            "email": email,
            "password": hash_password(password),
            "role": role.name,
            "role_id": role.id,
            "is_active": True,
        }
        user.update(windows_updates or {})

        return self.user_repository.create(user)
