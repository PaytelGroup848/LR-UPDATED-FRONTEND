from backend.extensions import db


class Server:

    collection = db["servers"]

    @staticmethod
    def create(data):

        server = {
            "name": data.get("name"),
            "host": data.get("host"),
            "username": data.get("username"),
            "password": data.get("password"),
            "domain": data.get("domain") or data.get("windows_domain") or data.get("hostname"),
            "port": data.get("port"),
            "is_active": data.get("is_active", True)
        }

        result = Server.collection.insert_one(server)
        server["_id"] = result.inserted_id
        return server

    @staticmethod
    def update(server_id, data):
        from bson import ObjectId

        return Server.collection.update_one(
            {"_id": ObjectId(server_id)},
            {"$set": data}
        )

    @staticmethod
    def delete(server_id):
        from bson import ObjectId

        return Server.collection.delete_one(
            {"_id": ObjectId(server_id)}
        )

    @staticmethod
    def get_by_id(server_id):
        from bson import ObjectId

        try:
            return Server.collection.find_one({"_id": ObjectId(server_id)})
        except:
            return None

    @staticmethod
    def find_all():
        return list(Server.collection.find())

    @staticmethod
    def find_active():
        return list(Server.collection.find({"is_active": True}))

    @staticmethod
    def to_dict(server):
        return {
            "id": str(server.get("_id")),
            "name": server.get("name"),
            "host": server.get("host"),
            "domain": server.get("domain") or server.get("windows_domain") or server.get("hostname"),
            "windows_domain": server.get("domain") or server.get("windows_domain") or server.get("hostname"),
            "ip_address": server.get("host"),
            "port": server.get("port"),
            "rdp_port": server.get("port"),
            "connection_type": "rdp",
            "os_type": "Windows",
            "description": "",
            "is_active": server.get("is_active"),
            "status": "online" if server.get("is_active") else "offline",
        }
