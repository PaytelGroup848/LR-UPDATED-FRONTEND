from datetime import datetime
from bson import ObjectId
from backend.extensions import db
from backend.models.application import PublishedApp


def _object_id(value):
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except Exception:
        return None
    

class ApplicationAssignment:

    collection = db["application_assignments"]
    apps_collection = db["published_apps"]

    @staticmethod
    def assign(user_id, app_id):
        user_id = _object_id(user_id)
        app_id = _object_id(app_id)
        if not user_id or not app_id:
            return None

        existing = ApplicationAssignment.collection.find_one({
            "user_id": user_id,
            "app_id": app_id
        })

        if existing:
            return None

        assignment = {
            "user_id": user_id,
            "app_id": app_id,
            "is_enabled": True,
            "assigned_at": datetime.utcnow()
        }

        result = ApplicationAssignment.collection.insert_one(assignment)
        assignment["_id"] = result.inserted_id
        return assignment

    @staticmethod
    def find(user_id, app_id):
        user_oid = _object_id(user_id)
        app_oid = _object_id(app_id)
        if not user_oid or not app_oid:
            return None
        user_ids = [user_oid, str(user_id)]
        app_ids = [app_oid, str(app_id)]
        return ApplicationAssignment.collection.find_one({
            "user_id": {"$in": user_ids},
            "app_id": {"$in": app_ids}
        })

    @staticmethod
    def to_dict(assignment):

        app = ApplicationAssignment.apps_collection.find_one({
            "_id": assignment.get("app_id")
        })

        return {
            "id": str(assignment.get("_id")),
            "user_id": str(assignment.get("user_id")) if assignment.get("user_id") else None,
            "app_id": str(assignment.get("app_id")) if assignment.get("app_id") else None,
            "is_enabled": assignment.get("is_enabled"),
            "assigned_at": assignment.get("assigned_at").isoformat() if assignment.get("assigned_at") else None,
            "app": PublishedApp.to_dict(app) if app else None,
        }
