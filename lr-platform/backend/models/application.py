from datetime import datetime
from bson import ObjectId
from backend.extensions import db


def _object_id(value):
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except Exception:
        return None


def _display_mode_from_launch_mode(app):
    launch_mode = app.get("launch_mode")
    if launch_mode == "desktop":
        return "full_desktop"
    if launch_mode in {"remote_app", "initial_program"}:
        return "remote_app"
    return "html5"


class PublishedApp:

    collection = db["published_apps"]
    servers_collection = db["servers"]
    assignments_collection = db["application_assignments"]

    @staticmethod
    def create(data):

        app = {
            "server_id": _object_id(data.get("server_id")),
            "name": data.get("name"),
            "slug": data.get("slug"),
            "icon": data.get("icon", "app"),
            "item_type": data.get("item_type"),
            "display_mode": data.get("display_mode") or data.get("view_mode"),
            "target": data.get("target"),
            "folder_path": data.get("folder_path"),
            "folder_permission": data.get("folder_permission"),
            "launch_mode": data.get("launch_mode", "remote_app"),
            "remote_app_program": data.get("remote_app_program"),
            "initial_program": data.get("initial_program"),
            "working_directory": data.get("working_directory"),
            "arguments": data.get("arguments"),
            "description": data.get("description", ""),
            "is_active": data.get("is_active", True),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # unique slug check
        if PublishedApp.collection.find_one({"slug": app["slug"]}):
            return None

        result = PublishedApp.collection.insert_one(app)
        app["_id"] = result.inserted_id
        return app

    @staticmethod
    def get_by_id(app_id):
        object_id = _object_id(app_id)
        if not object_id:
            return None
        return PublishedApp.collection.find_one({"_id": object_id})

    @staticmethod
    def assigned_to_user(user_id):
        oid = _object_id(user_id)
        user_ids = [str(user_id)]
        if oid:
            user_ids.append(oid)

        assignments = list(
            PublishedApp.assignments_collection.find({
                "user_id": {"$in": user_ids},
                "is_enabled": True
        })
    )

        app_ids = []

        for a in assignments:
            app_id = _object_id(a.get("app_id"))
            if app_id:
                app_ids.append(app_id)

        return list(
            PublishedApp.collection.find({
                "_id": {"$in": app_ids},
                "is_active": True
            }).sort("name", 1)
    )

    @staticmethod
    def update(app_id, data):
        object_id = _object_id(app_id)
        if not object_id:
            return None

        if "server_id" in data:
            data["server_id"] = _object_id(data.get("server_id"))
        data["updated_at"] = datetime.utcnow()

        return PublishedApp.collection.update_one(
            {"_id": object_id},
            {"$set": data}
        )

    @staticmethod
    def delete(app_id):
        object_id = _object_id(app_id)
        if not object_id:
            return None
        return PublishedApp.collection.delete_one({"_id": object_id})

    @staticmethod
    def to_dict(app, include_server=True):

        data = {
            "id": str(app.get("_id")),
            "server_id": str(app.get("server_id")) if app.get("server_id") else None,
            "name": app.get("name"),
            "slug": app.get("slug"),
            "icon": app.get("icon"),
            "item_type": app.get("item_type") or app.get("launch_mode"),
            "display_mode": app.get("display_mode") or _display_mode_from_launch_mode(app),
            "target": app.get("target") or app.get("remote_app_program") or app.get("folder_path"),
            "folder_path": app.get("folder_path"),
            "folder_permission": app.get("folder_permission"),
            "launch_mode": app.get("launch_mode"),
            "remote_app_program": app.get("remote_app_program"),
            "initial_program": app.get("initial_program"),
            "working_directory": app.get("working_directory"),
            "arguments": app.get("arguments"),
            "description": app.get("description", ""),
            "is_active": app.get("is_active"),
            "created_at": app.get("created_at").isoformat() if app.get("created_at") else None,
            "updated_at": app.get("updated_at").isoformat() if app.get("updated_at") else None,
        }

        if include_server and app.get("server_id"):
            server = PublishedApp.servers_collection.find_one({"_id": app["server_id"]})
            if server:
                data["server"] = {
                    "id": str(server.get("_id")),
                    "name": server.get("name"),
                    "ip_address": server.get("host"),
                    "rdp_port": server.get("port"),
                    "is_active": server.get("is_active"),
                }
                data["server_name"] = server.get("name")

        return data
