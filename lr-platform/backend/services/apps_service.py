import os
import re
from datetime import datetime
from uuid import uuid4

from bson import ObjectId
from flask import current_app

from backend.models.application import PublishedApp
from backend.models.assignment import ApplicationAssignment
from backend.models.user import User
from backend.services.desktop_shortcut_service import DesktopShortcutService


def _object_id(value):
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except Exception:
        return None


def _slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return slug or "app"


def _as_bool(value, default=True):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in {"false", "0", "no", "off"}


def _app_response(app):
    data = PublishedApp.to_dict(app)
    assignments = list(ApplicationAssignment.collection.find({
        "app_id": {"$in": [_object_id(app.get("_id")), str(app.get("_id"))]},
        "is_enabled": True,
    }))
    users = []
    for assignment in assignments:
        user = User.get_by_id(assignment.get("user_id"))
        if user:
            users.append(User.to_dict(user))
    data["assigned_users"] = users
    return data


class ApplicationService:

    @staticmethod
    def list_apps():
        apps = PublishedApp.collection.find().sort("name", 1)
        return {
            "success": True,
            "apps": [_app_response(app) for app in apps],
        }

    @staticmethod
    def create_app(data, user_id, ip_address):
        name = str(data.get("name") or "").strip()
        server_id = data.get("server_id")

        if not name or not server_id:
            return {"success": False, "message": "Name and server are required"}, 400

        payload = dict(data)
        payload["slug"] = payload.get("slug") or _slugify(name)
        payload["is_active"] = _as_bool(payload.get("is_active"), True)

        app = PublishedApp.create(payload)
        if not app:
            return {"success": False, "message": "Published item already exists"}, 409

        return {
            "success": True,
            "message": "Item published successfully",
            "app": _app_response(app),
        }, 201

    @staticmethod
    def update_app(app_id, data, user_id, ip_address):
        app = PublishedApp.get_by_id(app_id)
        if not app:
            return {"success": False, "message": "Published item not found"}, 404

        updates = dict(data)
        if "name" in updates and not updates.get("slug"):
            updates["slug"] = _slugify(updates.get("name"))
        if "is_active" in updates:
            updates["is_active"] = _as_bool(updates.get("is_active"), True)

        PublishedApp.update(app_id, updates)
        app = PublishedApp.get_by_id(app_id)

        return {
            "success": True,
            "message": "Item updated successfully",
            "app": _app_response(app),
        }, 200

    @staticmethod
    def delete_app(app_id, user_id, ip_address):
        result = PublishedApp.delete(app_id)
        if not result or result.deleted_count == 0:
            return {"success": False, "message": "Published item not found"}, 404

        app_oid = _object_id(app_id)
        ApplicationAssignment.collection.delete_many({
            "app_id": {"$in": [app_oid, str(app_id)] if app_oid else [str(app_id)]}
        })

        return {"success": True, "message": "Item deleted successfully"}, 200

    @staticmethod
    def assign_app(app_id, data, user_id, ip_address):
        target_user_id = data.get("user_id")
        app = PublishedApp.get_by_id(app_id)
        if not app:
            return {"success": False, "message": "Published item not found"}, 404
        target_user = User.get_by_id(target_user_id)
        if not target_user:
            return {"success": False, "message": "User not found"}, 404

        existing = ApplicationAssignment.find(target_user_id, app_id)
        if existing:
            ApplicationAssignment.collection.update_one(
                {"_id": existing["_id"]},
                {"$set": {"is_enabled": True, "assigned_at": datetime.utcnow()}},
            )
            assignment = ApplicationAssignment.collection.find_one({"_id": existing["_id"]})
        else:
            assignment = ApplicationAssignment.assign(target_user_id, app_id)

        shortcut_result = DesktopShortcutService.sync_assignment_shortcut(target_user, app)
        return {
            "success": True,
            "message": "Assignment saved",
            "assignment": ApplicationAssignment.to_dict(assignment),
            "shortcut": shortcut_result,
        }, 200

    @staticmethod
    def user_assignments(user_id):
        user = User.get_by_id(user_id)
        if not user:
            return {"success": False, "message": "User not found"}, 404

        user_oid = _object_id(user_id)
        user_ids = [str(user_id)]
        if user_oid:
            user_ids.append(user_oid)

        assignments = list(ApplicationAssignment.collection.find({
            "user_id": {"$in": user_ids},
            "is_enabled": True,
        }))
        assigned_app_ids = [str(item.get("app_id")) for item in assignments if item.get("app_id")]

        return {
            "success": True,
            "user": User.to_dict(user),
            "assigned_app_ids": assigned_app_ids,
            "assignments": [ApplicationAssignment.to_dict(item) for item in assignments],
            "available_apps": [PublishedApp.to_dict(app) for app in PublishedApp.collection.find({"is_active": True}).sort("name", 1)],
        }, 200

    @staticmethod
    def bulk_assign_apps(user_ids, app_ids, enabled, admin_user_id, ip_address):
        changed = 0
        for user_id in user_ids or []:
            for app_id in app_ids or []:
                if enabled:
                    result, status = ApplicationService.assign_app(app_id, {"user_id": user_id}, admin_user_id, ip_address)
                    if status == 200 and result.get("success"):
                        changed += 1
                else:
                    result, status = ApplicationService.unassign_app(app_id, user_id, admin_user_id, ip_address)
                    if status == 200 and result.get("success"):
                        changed += 1

        return {
            "success": True,
            "message": "Assignments updated",
            "changed": changed,
        }

    @staticmethod
    def upload_software(uploaded_file, admin_user_id, ip_address):
        if not uploaded_file:
            return {
                "success": False,
                "error": "file is required"
            }, 400

        filename = os.path.basename(uploaded_file.filename or "")

        if not filename.lower().endswith((".exe", ".msi", ".bat", ".cmd")):
            return {
                "success": False,
                "error": "Only executable installer files are allowed"
            }, 400

        upload_dir = os.path.join(
            current_app.instance_path,
            "software_uploads"
        )
        os.makedirs(upload_dir, exist_ok=True)

        stored_name = (
            f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            f"-{uuid4().hex[:8]}"
            f"-{filename}"
        )
        file_path = os.path.join(upload_dir, stored_name)

        uploaded_file.save(file_path)

        return {
            "success": True,
            "file": {
                "name": stored_name,
                "path": file_path,
                "size": os.path.getsize(file_path)
            }
        }, 201

    @staticmethod
    def unassign_app(app_id, user_id, admin_user_id, ip_address):
        assignment = ApplicationAssignment.find(user_id, app_id)
        if not assignment:
            return {"success": False, "message": "Assignment not found"}, 404

        user = User.get_by_id(user_id)
        app = PublishedApp.get_by_id(app_id)
        ApplicationAssignment.collection.delete_one({"_id": assignment["_id"]})
        shortcut_result = (
            DesktopShortcutService.remove_assignment_shortcut(user, app)
            if user and app
            else {"success": False, "message": "Shortcut sync skipped.", "skipped": True}
        )
        return {"success": True, "message": "Assignment removed", "shortcut": shortcut_result}, 200


AppService = ApplicationService
