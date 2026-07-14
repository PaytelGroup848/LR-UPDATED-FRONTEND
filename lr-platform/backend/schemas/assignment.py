from datetime import datetime

from pydantic import BaseModel


class AssignmentCreateRequest(BaseModel):
    user_id: str
    app_id: str


class AssignmentResponse(BaseModel):
    id: str
    user_id: str
    app_id: str
    is_enabled: bool = True
    assigned_at: datetime | None = None
