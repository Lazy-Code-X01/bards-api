from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NotificationOut(BaseModel):
    id: str
    type: str
    source_message_id: Optional[str] = None
    channel_id: Optional[str] = None
    read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationsPageOut(BaseModel):
    notifications: list[NotificationOut]
    next_cursor: Optional[str] = None


class UnreadCountOut(BaseModel):
    count: int
