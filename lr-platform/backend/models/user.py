from datetime import datetime
from backend.extensions import db


class MongoUser(dict):
    @property
    def id(self):
        return str(self.get("_id"))

    @property
    def username(self):
        return self.get("username")

    @username.setter
    def username(self, value):
        self["username"] = value

    @property
    def password(self):
        return self.get("password")

    @password.setter
    def password(self, value):
        self["password"] = value

    @property
    def email(self):
        return self.get("email")

    @email.setter
    def email(self, value):
        self["email"] = value

    @property
    def role(self):
        return self.get("role")

    @property
    def role_id(self):
        return self.get("role_id")

    @property
    def is_active(self):
        return bool(self.get("is_active"))

    @is_active.setter
    def is_active(self, value):
        self["is_active"] = bool(value)

    @property
    def two_factor_enabled(self):
        return bool(self.get("two_factor_enabled"))

    @property
    def two_factor_secret(self):
        return self.get("two_factor_secret")

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.get("_id"))

    def has_role(self, *roles):
        return User.has_role(self, *roles)

    def to_dict(self):
        return User.to_dict(self)

    def set_role(self, role):
        self["role"] = User.normalize_role(role)
        User.update(self.id, {"role": self["role"]})


class User:

    collection = db["users"]

    @staticmethod
    def _wrap(user):
        return MongoUser(user) if user else None

    ROLES = ('Super Admin', 'Admin', 'Manager', 'Viewer', 'User')
    ROLE_ALIASES = {
        'Superadmin': 'Super Admin',
        'Super Admin': 'Super Admin',
    }
    ROLE_COMPARE_ALIASES = {
        "SUPERADMIN": "SUPER_ADMIN",
        "SUPER ADMIN": "SUPER_ADMIN",
    }

    @classmethod
    def _role_key(cls, role):
        value = str(role or "").strip().upper().replace("-", "_").replace(" ", "_")
        return cls.ROLE_COMPARE_ALIASES.get(value, value)

    # ✅ CREATE USER
    @staticmethod
    def create(username, password, role="User"):

        role = User.normalize_role(role)

        # unique username check
        if User.collection.find_one({"username": username}):
            return None

        user = {
            "username": username,
            "password": password,
            "role": role,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login_at": None,
            "two_factor_enabled": False,
            "two_factor_secret": None,
            "assigned_app": None,
            "windows_username": None,
            "windows_domain": None,
            "windows_password": None,
            "windows_account_enabled": False,
        }

        result = User.collection.insert_one(user)
        user["_id"] = result.inserted_id
        return User._wrap(user)

    # ✅ ROLE NORMALIZATION
    @classmethod
    def normalize_role(cls, role):
        value = (role or 'User').strip().title()
        value = cls.ROLE_ALIASES.get(value, value)
        if value not in cls.ROLES:
            raise ValueError(f'Invalid role. Allowed roles: {", ".join(cls.ROLES)}')
        return value

    # ✅ ROLE CHECK
    @staticmethod
    def has_role(user, *roles):
        current_role = User._role_key(user.get("role"))
        required_roles = {User._role_key(role) for role in roles}
        if current_role == "SUPER_ADMIN":
            return True
        return current_role in required_roles

    # ✅ FLAGS
    @staticmethod
    def is_admin(user):
        return User._role_key(user.get("role")) in ("ADMIN", "SUPER_ADMIN")

    @staticmethod
    def is_manager(user):
        return User._role_key(user.get("role")) in ("MANAGER", "OPERATOR")

    # ✅ UPDATE LAST LOGIN
    @staticmethod
    def update_login(user_id):
        from bson import ObjectId

        return User.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"last_login_at": datetime.utcnow()}}
        )

    # ✅ FIND USER
    @staticmethod
    def get_by_id(user_id):
        from bson import ObjectId
        try:
            return User._wrap(User.collection.find_one({"_id": ObjectId(user_id)}))
        except:
            return None

    @staticmethod
    def find_by_username(username):
        if not username:
            return None
        return User._wrap(User.collection.find_one({"username": username}))

    @staticmethod
    def username_exists(username):
        return User.collection.find_one({"username": username}) is not None

    # ✅ UPDATE USER
    @staticmethod
    def update(user_id, data):
        from bson import ObjectId

        if "role" in data:
            data["role"] = User.normalize_role(data["role"])

        return User.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": data}
        )

    # ✅ DELETE USER
    @staticmethod
    def delete(user_id):
        from bson import ObjectId
        return User.collection.delete_one({"_id": ObjectId(user_id)})

    # ✅ AUTH COMPATIBILITY (Flask-Login type)
    @staticmethod
    def get_id(user):
        return str(user.get("_id"))

    @staticmethod
    def is_authenticated(user):
        return True

    @staticmethod
    def is_anonymous(user):
        return False

    # ✅ TO DICT
    @staticmethod
    def to_dict(user):
        windows_username = user.get("windows_username")
        return {
            "id": str(user.get("_id")),
            "username": user.get("username"),
            "email": user.get("email"),
            "role": user.get("role"),
            "role_id": user.get("role_id"),
            "is_active": bool(user.get("is_active")),
            "created_at": user.get("created_at").isoformat() if user.get("created_at") else None,
            "last_login_at": user.get("last_login_at").isoformat() if user.get("last_login_at") else None,
            "two_factor_enabled": bool(user.get("two_factor_enabled")),
            "windows_username": windows_username,
            "windows_domain": user.get("windows_domain"),
            "windows_account_enabled": bool(user.get("windows_account_enabled") and windows_username),
            "windows_account_configured": bool(windows_username and user.get("windows_password")),
        }
