from backend.models.activity_log import ActivityLog


class AuditService:
    @staticmethod
    def log(
        action,
        *,
        user=None,
        user_id=None,
        category="system",
        server_id=None,
        session_id=None,
        ip_address=None,
        success=True,
        reason=None,
        metadata=None,
    ):
        actor_id = user_id or getattr(user, "id", None)
        actor_role = getattr(user, "role", None) if user is not None else None
        return ActivityLog.log(
            user_id=actor_id,
            action=action,
            category=category,
            server_id=server_id,
            session_id=session_id,
            ip_address=ip_address,
            success=success,
            reason=reason,
            actor_role=actor_role,
            metadata=metadata or {},
        )

    @staticmethod
    def list(limit=100, user_id=None):
        return [ActivityLog.to_dict(item) for item in ActivityLog.recent(limit, user_id=user_id)]
