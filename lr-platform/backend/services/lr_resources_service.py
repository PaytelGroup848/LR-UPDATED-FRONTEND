from backend.models.application import PublishedApp
from backend.services.portal_service import PortalService


def _resource_type(app):
    item_type = str((app or {}).get("item_type") or "").strip().lower()
    if item_type == "folder" or (app or {}).get("folder_path"):
        return "folder"
    return "application"


def _resource_icon(app, resource_type):
    icon = str((app or {}).get("icon") or "").strip()
    if icon.startswith(("/", "http://", "https://")):
        return icon
    return "/lr-icons/folder.svg" if resource_type == "folder" else "/lr-icons/application.svg"


def _resource_payload(app):
    resource_type = _resource_type(app)
    return {
        "id": str(app.get("_id")),
        "name": app.get("name") or ("Folder" if resource_type == "folder" else "Application"),
        "icon": _resource_icon(app, resource_type),
        "type": resource_type,
    }


def _is_published_remote_app(app):
    item_type = str((app or {}).get("item_type") or "").strip().lower()
    return item_type not in {"desktop", "folder"} and bool(
        str((app or {}).get("remote_app_program") or "").strip()
    )


class LrResourcesService:
    @staticmethod
    def my_resources(user_id):
        assigned_apps = PublishedApp.assigned_to_user(user_id)
        resources = [_resource_payload(app) for app in assigned_apps if _is_published_remote_app(app)]
        return {
            "success": True,
            "logo": "/lr-remote-logo.png",
            "applications": [item for item in resources if item["type"] == "application"],
            "folders": [],
        }, 200

    @staticmethod
    def launch_resource(data, user_id, ip_address, user_agent):
        resource_id = str((data or {}).get("resource_id") or "").strip()
        requested_type = str((data or {}).get("type") or "").strip().lower()
        connection_type = str((data or {}).get("connection_type") or "").strip().lower()
        if connection_type != "remoteapp":
            return {"success": False, "error": "connection_type must be remoteapp"}, 400
        if not resource_id:
            return {"success": False, "error": "resource_id is required"}, 400
        if requested_type not in {"application", "folder"}:
            return {"success": False, "error": "type must be application or folder"}, 400

        app = PublishedApp.get_by_id(resource_id)
        if not app:
            return {"success": False, "error": "Resource not found"}, 404

        actual_type = _resource_type(app)
        if actual_type != requested_type:
            return {"success": False, "error": "Resource type mismatch"}, 400

        if requested_type != "application":
            return {"success": False, "error": "RemoteApp mode can only launch a published application"}, 400

        return PortalService.launch_remote_app(
            app_id=resource_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
