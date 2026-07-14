import hmac
from datetime import datetime
from functools import wraps
from typing import Any, cast

from bson import ObjectId
from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from jinja2 import TemplateNotFound
from werkzeug.routing import BuildError
from werkzeug.security import check_password_hash, generate_password_hash

from backend.models.user import User
from backend.services.auth_service import AuthService
from backend.services.auth_service import UserService
from backend.models.login_link import LoginLink

class ActivityLog:

    @staticmethod
    def log(*args, **kwargs):
        return None

auth = Blueprint("auth", __name__)


def _get_request_data():
    return request.get_json(silent=True) or request.form


def _object_id(value):
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except Exception:
        return None


def _doc_get(doc, key, default=None):
    if isinstance(doc, dict):
        return doc.get(key, default)
    return getattr(doc, key, default)


def _doc_id(doc):
    if not doc:
        return None
    return _doc_get(doc, "_id") or _doc_get(doc, "id")


def _current_user_id():
    return _doc_id(current_user)


def _user_to_dict(user):
    if hasattr(User, "to_dict"):
        return User.to_dict(user)
    return user.to_dict()


def _login_link_to_dict(link):
    if hasattr(LoginLink, "to_dict"):
        return LoginLink.to_dict(link)
    return link.to_dict()


def _create_user(username, password, role):
    if hasattr(User, "create"):
        return User.create(username, password, role)

    payload = {
        "username": username,
        "password": password,
        "role": role,
        "is_active": True,
        "created_at": datetime.utcnow(),
    }

    result = User.collection.insert_one(payload)
    return User.get_by_id(result.inserted_id)

def _set_user_fields(user_id, updates):
    if updates:
        User.collection.update_one({"_id": user_id}, {"$set": updates})
    return User.get_by_id(user_id)


def _password_matches(user, password):
    stored = _doc_get(user, "password", "") or ""
    is_hash = stored.startswith(("scrypt:", "pbkdf2:", "argon2:"))
    if is_hash and check_password_hash(stored, password):
        return True
    if not is_hash and hmac.compare_digest(stored, password):
        hashed_password = generate_password_hash(password)
        _set_user_fields(_doc_id(user), {"password": hashed_password})
        ActivityLog.log(_doc_id(user), "password_hash_migrated", "auth", ip_address=request.remote_addr)
        return True
    return False


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user.has_role(*roles):
                return jsonify({"message": "Forbidden", "required_roles": list(roles)}), 403
            return view(*args, **kwargs)

        return wrapped

    return decorator


admin_required = role_required("Admin")


def _portal_home_url():
    configured_url = current_app.config.get("PORTAL_HOME_URL")
    if configured_url:
        return configured_url
    try:
        return url_for("portal.portal_home")
    except BuildError:
        return "/portal/"


def _connection_type(value):
    normalized = str(value or "web").strip().lower()
    aliases = {
        "html5": "web",
        "remote_app": "remoteapp",
        "full_desktop": "desktop",
    }
    return aliases.get(normalized, normalized)


@auth.route("/register", methods=["POST"])
def register():
    data = _get_request_data()

    user, error = AuthService.register_user(
        data.get("username"),
        data.get("password")
    )

    if error:
        status = 400 if "required" in error else 409
        return jsonify({"message": error}), status

    return jsonify({
        "message": "User registered successfully",
        **_user_to_dict(user)
    }), 201

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        try:
            return render_template("index.html")
        except TemplateNotFound:
            return jsonify({
                "message": "Login UI is served by the frontend. POST username and password to this endpoint.",
                "endpoint": "/login",
            }), 200

    data = _get_request_data()
    connection_type = _connection_type(data.get("connection_type") or data.get("view_mode"))
    if connection_type not in {"web", "remoteapp", "desktop"}:
        return jsonify({"message": "connection_type must be web, remoteapp, or desktop"}), 400

    user, message, status = AuthService.login(
        data.get("username"),
        data.get("password"),
        data.get("token") or data.get("two_factor_code")
    )

    if not user:
        extra = {}
        if status == 401 and "Two-factor" in message:
            extra["requires_2fa"] = True

        return jsonify({"message": message, **extra}), status

    session["connection_type"] = connection_type

    return jsonify({
        "message": message,
        "redirect": "/web-access" if connection_type == "remoteapp" else _portal_home_url(),
        "connection_type": connection_type,
        "user": _user_to_dict(user),
    }), 200


@auth.route("/login-link/<token>", methods=["GET"])
def login_link(token):
    user, error, status = AuthService.login_via_link(token)

    if error:
        return jsonify({
            "message": "Login link is invalid, expired, revoked, or already used"
        }), status

    if (
        request.args.get("format") == "json"
        or request.accept_mimetypes.best == "application/json"
        or request.is_json
    ):
        return jsonify({
            "success": True,
            "message": "Login successful",
            "redirect": "/portal",
            "user": _user_to_dict(user),
        }), 200

    return redirect(_portal_home_url())


@auth.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    AuthService.logout()

    if request.method == "GET":
        return redirect(url_for("auth.login"))

    return jsonify({"message": "Logged out successfully"}), 200


@auth.route("/me", methods=["GET"])
@login_required
def me():
    response, code = AuthService.me(current_user)
    return jsonify(response), code


@auth.route("/users", methods=["GET"])
@admin_required
def users():
    response, code = AuthService.list_users(request.args)
    return jsonify(response), code

@auth.route("/users", methods=["POST"])
@admin_required
def create_user():
    response, code = AuthService.create_user(
        request.get_json(silent=True) or request.form,
        _current_user_id(),
        request.remote_addr
    )
    return jsonify(response), code

@auth.route("/users/<user_id>", methods=["PATCH", "POST"])
@admin_required
def update_user(user_id):
    response, code = AuthService.update_user(
        user_id,
        request.get_json(silent=True) or request.form,
        _current_user_id(),
        request.remote_addr
    )
    return jsonify(response), code


@auth.route("/users/<user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    response, code = UserService.delete_user(
        user_id,
        _current_user_id(),
        request.remote_addr
    )
    return jsonify(response), code


@auth.route("/users/bulk-delete", methods=["POST"])
@admin_required
def bulk_delete_users():
    data = _get_request_data()

    response, code = UserService.bulk_delete(
        data.get("user_ids", []),
        _current_user_id(),
        request.remote_addr
    )
    return jsonify(response), code

@auth.route("/users/import-csv", methods=["POST"])
@admin_required
def import_users_csv():
    import csv, io

    uploaded = request.files.get("file")
    if not uploaded:
        return jsonify({"message": "CSV file is required"}), 400

    text = uploaded.read().decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))

    response, code = UserService.import_csv(
        rows,
        _current_user_id(),
        request.remote_addr
    )
    return jsonify(response), code

@auth.route("/users/<user_id>/role", methods=["PATCH", "POST"])
@admin_required
def update_user_role(user_id):
    response, code = UserService.update_role(
        user_id,
        _get_request_data(),
        _current_user_id(),
        request.remote_addr
    )
    return jsonify(response), code
