from bson import ObjectId

from backend.models.role import Role
from backend.models.user import User


class UserRepository:
    def __init__(self, db):
        self.collection = db["users"]

    def _wrap(self, user):
        return User._wrap(user)

    def _id_filter(self, user_id):
        if isinstance(user_id, ObjectId):
            return {"_id": user_id}
        try:
            return {"_id": ObjectId(str(user_id))}
        except Exception:
            return {"id": user_id}

    def get_by_id(self, user_id):
        return self._wrap(self.collection.find_one(self._id_filter(user_id)))

    def get_by_username(self, username: str):
        return self._wrap(self.collection.find_one({"username": username}))

    def get_by_email(self, email: str):
        return self._wrap(self.collection.find_one({"email": email}))

    def exists_by_username(self, username: str) -> bool:
        return self.collection.find_one({"username": username}) is not None

    def exists_by_email(self, email: str) -> bool:
        return self.collection.find_one({"email": email}) is not None

    def create(self, user):
        document = dict(user)
        role_name = document.get("role") or document.get("role_name") or "USER"
        role = Role.get_by_name(role_name)
        document["role"] = role.name if role else str(role_name).upper()
        document["role_id"] = role.id if role else None
        document.setdefault("is_active", True)
        result = self.collection.insert_one(document)
        document["_id"] = result.inserted_id
        return self._wrap(document)

    def update(self, user):
        updates = dict(user)
        user_id = updates.pop("_id", None) or updates.pop("id", None)
        if not user_id:
            return user
        self.collection.update_one(self._id_filter(user_id), {"$set": updates})
        return self.get_by_id(user_id)

    def delete(self, user) -> None:
        user_id = user.get("_id") if isinstance(user, dict) else getattr(user, "id", None)
        if user_id:
            self.collection.delete_one(self._id_filter(user_id))

    def get_all(self):
        return [self._wrap(item) for item in self.collection.find().sort("username", 1)]
