from backend.services.audit_service import AuditService


class ActivityLogService:

    @staticmethod
    def get_logs(limit=100, user_id=None):
        return {
            "success": True,
            "logs": AuditService.list(limit, user_id=user_id),
        }
