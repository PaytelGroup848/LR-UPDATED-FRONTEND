from backend.extensions import db


def _index_keys(index):
    if isinstance(index, tuple) and len(index) == 2 and isinstance(index[0], str):
        return [index]
    return index


class IndexService:
    _ensured = False

    @classmethod
    def ensure_indexes(cls):
        if cls._ensured:
            return

        specs = {
            "users": [
                ("username", 1),
                ("role", 1),
                ("is_active", 1),
            ],
            "rdp_sessions": [
                ("user_id", 1),
                ("status", 1),
                ("started_at", -1),
                [("user_id", 1), ("status", 1), ("started_at", -1)],
            ],
            "activity_logs": [
                ("user_id", 1),
                ("timestamp", -1),
                ("created_at", -1),
                [("user_id", 1), ("timestamp", -1)],
            ],
            "agents": [
                ("username", 1),
                ("status", 1),
                ("last_seen", -1),
            ],
            "user_policies": [
                ("user_id", 1),
            ],
            "application_assignments": [
                ("user_id", 1),
                ("app_id", 1),
                [("user_id", 1), ("is_enabled", 1)],
            ],
            "login_links": [
                ("user_id", 1),
                ("token", 1),
                ("created_at", -1),
            ],
        }

        for collection_name, indexes in specs.items():
            collection = db[collection_name]
            for index in indexes:
                keys = _index_keys(index)
                try:
                    collection.create_index(keys, background=True)
                except TypeError:
                    collection.create_index(keys)
        cls._ensured = True
