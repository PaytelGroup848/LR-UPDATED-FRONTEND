from backend.extensions import db


class MongoRole(dict):
    @property
    def id(self):
        return self.get("id")

    @property
    def name(self):
        return self.get("name")

    @property
    def description(self):
        return self.get("description")


class Role:
    collection = db["roles"]

    DEFAULT_ROLES = [
        {"id": 1, "name": "SUPER_ADMIN", "description": "Full platform access"},
        {"id": 2, "name": "ADMIN", "description": "Administrative access"},
        {"id": 3, "name": "OPERATOR", "description": "Operational access"},
        {"id": 4, "name": "USER", "description": "Standard user access"},
    ]

    @staticmethod
    def _wrap(role):
        return MongoRole(role) if role else None

    @classmethod
    def ensure_defaults(cls):
        for role in cls.DEFAULT_ROLES:
            cls.collection.update_one(
                {"name": role["name"]},
                {"$setOnInsert": role},
                upsert=True,
            )

    @classmethod
    def get_by_name(cls, name):
        cls.ensure_defaults()
        if not name:
            return None
        return cls._wrap(cls.collection.find_one({"name": str(name).upper()}))

    @classmethod
    def get_by_id(cls, role_id):
        cls.ensure_defaults()
        try:
            role_id = int(role_id)
        except (TypeError, ValueError):
            return None
        return cls._wrap(cls.collection.find_one({"id": role_id}))

    @classmethod
    def get_all(cls):
        cls.ensure_defaults()
        return [cls._wrap(item) for item in cls.collection.find().sort("id", 1)]
