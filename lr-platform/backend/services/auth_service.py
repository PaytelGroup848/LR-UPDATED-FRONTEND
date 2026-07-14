from datetime import datetime

import re
from flask_login import login_user, logout_user

from backend.models.login_link import LoginLink
from backend.models.user import User
from backend.security.credential_crypto import encrypt_secret
from backend.services.windows_account_service import WindowsAccountService
from shared.security.password import hash_password, verify_password


def _clean_text(value):
    return str(value or "").strip()


def _user_response(user):
    return User.to_dict(user) if user else None


def _password_matches(password, stored_password):
    if not password or not stored_password:
        return False

    try:
        if verify_password(password, stored_password):
            return True
    except Exception:
        pass

    return password == stored_password


def _normalize_bool(value, default=True):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in {"false", "0", "no", "off"}


def _sync_windows_credentials_from_login(user, username, password):
    if not user or not username or not password:
        return

    windows_username = _clean_text(user.get("windows_username"))
    if windows_username and windows_username.lower() != username.lower():
        return

    updates = {
        "windows_username": windows_username or username,
        "windows_password": encrypt_secret(password),
        "windows_account_enabled": True,
    }
    if "windows_domain" not in user:
        updates["windows_domain"] = None

    User.update(user.id, updates)
    user.update(updates)


def _windows_account_updates(data, existing_user=None):
    updates = {}

    for source_key, target_key in (
        ("windows_username", "windows_username"),
        ("rdp_username", "windows_username"),
        ("windows_domain", "windows_domain"),
        ("rdp_domain", "windows_domain"),
    ):
        if source_key in data:
            updates[target_key] = _clean_text(data.get(source_key)) or None

    password_value = None
    password_provided = False
    for key in ("windows_password", "rdp_password"):
        if key in data:
            password_value = data.get(key)
            password_provided = True
            break
    if password_provided:
        updates["windows_password"] = encrypt_secret(password_value)

    if "windows_account_enabled" in data:
        updates["windows_account_enabled"] = _normalize_bool(data.get("windows_account_enabled"), False)
    elif "rdp_enabled" in data:
        updates["windows_account_enabled"] = _normalize_bool(data.get("rdp_enabled"), False)
    elif existing_user is None and updates.get("windows_username"):
        updates["windows_account_enabled"] = True

    if updates.get("windows_username") is None and "windows_username" in updates:
        updates["windows_account_enabled"] = False
        updates["windows_password"] = None
        updates["windows_domain"] = None

    return updates


class AuthService:

    @staticmethod
    def register_user(username, password):
        username = _clean_text(username)
        password = str(password or "")

        if not username or not password:
            return None, "Username and password are required"

        if User.username_exists(username):
            return None, "Username already exists"

        user = User.create(username, hash_password(password), "User")
        if not user:
            return None, "Username already exists"

        return user, None

    @staticmethod
    def login(username, password, token=None):
        username = _clean_text(username)
        password = str(password or "")

        if not username or not password:
            return None, "Username and password are required", 400

        user = User.find_by_username(username)
        if not user or not _password_matches(password, user.get("password")):
            return None, "Invalid username or password", 401

        if not user.is_active:
            return None, "User is disabled", 401

        if user.two_factor_enabled and not _clean_text(token):
            return None, "Two-factor code is required", 401

        # 2FA verification is not configured yet; keep the response explicit.
        if user.two_factor_enabled:
            return None, "Two-factor verification is not configured", 501

        _sync_windows_credentials_from_login(user, username, password)
        login_user(user)
        User.update_login(user.id)
        return user, "Login successful", 200

    @staticmethod
    def login_via_link(token):
        token = _clean_text(token)
        link = LoginLink.get_by_token(token)
        if link is None or not LoginLink.is_valid(link):
            return None, "Invalid login link", 403

        user_id = link.get("user_id")
        if not user_id:
            return None, "Login link is not assigned to a user", 403

        user = User.get_by_id(user_id)
        if not user or not user.is_active:
            return None, "User is disabled or not found", 403

        login_user(user)
        User.update_login(user.id)
        if link.get("one_time"):
            LoginLink.mark_used(token)

        return user, None, 200

    @staticmethod
    def logout():
        logout_user()
        return True

    @staticmethod
    def me(user):
        return {
            "success": True,
            "user": _user_response(user),
        }, 200

    @staticmethod
    def list_users(params):
        params = params or {}
        try:
            limit = min(max(int(params.get("limit", 500)), 1), 1000)
        except (TypeError, ValueError):
            limit = 500
        try:
            offset = max(int(params.get("offset", 0)), 0)
        except (TypeError, ValueError):
            offset = 0

        query = {}
        search = _clean_text(params.get("q") or params.get("search"))
        if search:
            query["username"] = {"$regex": re.escape(search), "$options": "i"}
        role = _clean_text(params.get("role"))
        if role:
            query["role"] = role

        cursor = User.collection.find(query).sort("username", 1).skip(offset).limit(limit)
        users = [User.to_dict(user) for user in cursor]
        total = User.collection.count_documents(query)
        return {
            "success": True,
            "users": users,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(users) < total,
        }, 200

    @staticmethod
    def create_user(data, actor_id, ip_address):
        username = _clean_text(data.get("username"))
        password = str(data.get("password") or "")
        role = data.get("role") or data.get("role_name") or "User"
        email = _clean_text(data.get("email"))

        if not username or not password:
            return {"message": "Username and password are required"}, 400

        if User.username_exists(username):
            return {"message": "Username already exists"}, 409

        windows_updates, windows_error = WindowsAccountService.build_updates(
            data,
            default_username=username,
            default_password=password,
            create_local_account=WindowsAccountService.normalize_bool(
                data.get("windows_create_account"),
                True,
            ),
        )
        if windows_error:
            return {"message": windows_error}, 400

        try:
            user = User.create(username, hash_password(password), role)
        except ValueError as error:
            return {"message": str(error)}, 400
        if not user:
            return {"message": "Username already exists"}, 409

        user_id = user.id

        updates = {
            "created_at": datetime.utcnow(),
            "created_by": actor_id,
        }
        if email:
            updates["email"] = email
        updates.update(windows_updates or {})

        if updates:
            User.update(user_id, updates)
            user = User.get_by_id(user_id)

        return {
            "success": True,
            "message": "User created successfully",
            "user": _user_response(user),
        }, 201

    @staticmethod
    def update_user(user_id, data, actor_id, ip_address):
        user = User.get_by_id(user_id)
        if not user:
            return {"message": "User not found"}, 404

        updates = {
            "updated_at": datetime.utcnow(),
            "updated_by": actor_id,
        }

        username = _clean_text(data.get("username"))
        if username and username != user.username:
            existing = User.find_by_username(username)
            if existing and existing.id != user.id:
                return {"message": "Username already exists"}, 409
            updates["username"] = username

        email = _clean_text(data.get("email"))
        if email:
            updates["email"] = email

        password = data.get("password")
        if password:
            updates["password"] = hash_password(str(password))

        role = data.get("role") or data.get("role_name")
        if role:
            try:
                updates["role"] = User.normalize_role(role)
            except ValueError as error:
                return {"message": str(error)}, 400

        if "is_active" in data:
            updates["is_active"] = _normalize_bool(data.get("is_active"))

        updates.update(_windows_account_updates(data, user))

        User.update(user_id, updates)
        updated_user = User.get_by_id(user_id)

        return {
            "success": True,
            "message": "User updated successfully",
            "user": _user_response(updated_user),
        }, 200


class UserService:

    @staticmethod
    def delete_user(user_id, actor_id, ip_address):
        result = User.delete(user_id)
        if result.deleted_count == 0:
            return {"message": "User not found"}, 404

        return {
            "success": True,
            "message": "User deleted successfully"
        }, 200

    @staticmethod
    def bulk_delete(user_ids, actor_id, ip_address):
        deleted = 0
        for user_id in user_ids or []:
            result = User.delete(user_id)
            deleted += result.deleted_count

        return {
            "success": True,
            "message": "Users deleted successfully",
            "deleted": deleted
        }, 200

    @staticmethod
    def import_csv(rows, actor_id, ip_address):
        created = 0
        skipped_rows = []

        for index, row in enumerate(rows or [], start=1):
            username = _clean_text(row.get("username"))
            password = str(row.get("password") or "")
            role = row.get("role") or row.get("role_name") or "User"

            if not username or not password:
                skipped_rows.append({"row": index, "message": "Username and password are required"})
                continue

            response, code = AuthService.create_user(row, actor_id, ip_address)
            if code == 201:
                created += 1
            else:
                skipped_rows.append({"row": index, "message": response.get("message", "Skipped")})

        return {
            "success": True,
            "message": "CSV import completed",
            "created": created,
            "skipped_rows": skipped_rows
        }, 200

    @staticmethod
    def update_role(user_id, role_data, actor_id, ip_address):
        return AuthService.update_user(
            user_id,
            {"role": role_data.get("role") or role_data.get("role_name")},
            actor_id,
            ip_address
        )
