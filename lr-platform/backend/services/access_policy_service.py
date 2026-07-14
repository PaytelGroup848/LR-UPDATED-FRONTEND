from bson import ObjectId

from backend.models.application import PublishedApp
from backend.models.assignment import ApplicationAssignment
from backend.models.rdp_session import RdpSession
from backend.models.server import Server
from backend.models.user import User


def _object_id(value):
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except Exception:
        return None


def _id_variants(value):
    variants = [str(value)]
    object_id = _object_id(value)
    if object_id:
        variants.append(object_id)
    return variants


class AccessPolicyService:
    @staticmethod
    def is_admin(user):
        return bool(user and User.is_admin(user))

    @staticmethod
    def has_role(user, *roles):
        return bool(user and hasattr(user, "has_role") and user.has_role(*roles))

    @staticmethod
    def can_launch_app(user_id, app_id):
        app = PublishedApp.get_by_id(app_id)
        if not app or app.get("is_active") is False:
            return False, "Application not found", None
        assignment = ApplicationAssignment.find(user_id, app_id)
        if not assignment or assignment.get("is_enabled") is False:
            return False, "Application is not assigned to this user", app
        server = Server.get_by_id(app.get("server_id"))
        if not server or server.get("is_active") is False:
            return False, "Assigned server is not available", app
        return True, None, app

    @staticmethod
    def can_launch_server(user, server_id):
        server = Server.get_by_id(server_id)
        if not server or server.get("is_active") is False:
            return False, "Server not found", None
        if AccessPolicyService.has_role(user, "Admin", "Manager"):
            return True, None, server
        return True, None, server

    @staticmethod
    def can_view_session(user, session_id):
        object_id = _object_id(session_id)
        if not object_id:
            return False, "Session not found", None
        session = RdpSession.collection.find_one({"_id": object_id})
        if not session:
            return False, "Session not found", None
        if AccessPolicyService.has_role(user, "Admin", "Manager"):
            return True, None, session
        if session.get("user_id") in _id_variants(getattr(user, "id", None)):
            return True, None, session
        return False, "Session belongs to another user", session

    @staticmethod
    def can_reconnect_session(user, session_id):
        allowed, reason, session = AccessPolicyService.can_view_session(user, session_id)
        if not allowed:
            return allowed, reason, session
        if session.get("status") not in {"active", "pending"}:
            return False, "Session is not reconnectable", session
        return True, None, session

    @staticmethod
    def can_view_stream(user, agent_id, session_id=None):
        if not user or not user.is_authenticated:
            return False, "Authentication required"
        if AccessPolicyService.has_role(user, "Admin", "Manager"):
            if session_id:
                allowed, reason, _ = AccessPolicyService.can_view_session(user, session_id)
                if not allowed:
                    return False, reason
            return True, None
        if session_id:
            allowed, reason, _ = AccessPolicyService.can_view_session(user, session_id)
            if not allowed:
                return False, reason
            return True, None
        return False, "Stream viewing requires a valid session"

    @staticmethod
    def can_control_stream(user, agent_id, action=None, session_id=None):
        if not user or not user.is_authenticated:
            return False, "Authentication required"
        if session_id:
            allowed, reason, _ = AccessPolicyService.can_view_session(user, session_id)
            if not allowed:
                return False, reason
        if AccessPolicyService.has_role(user, "Admin"):
            return True, None
        return False, "Stream control requires Admin role"

    @staticmethod
    def can_record_stream(user, agent_id, session_id=None):
        if AccessPolicyService.has_role(user, "Admin", "Manager"):
            return True, None
        return False, "Recording requires Admin or Manager role"
