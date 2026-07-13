from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from schemas.user import UserOut


class ReactionOut(BaseModel):
    emoji: str
    count: int
    reacted: bool


class MessageOut(BaseModel):
    id: str
    channel_id: str
    sender: Optional[UserOut] = None
    content: str
    is_system: bool
    is_agent: bool
    system_type: Optional[str] = None
    system_action: Optional[dict] = None
    pinned: bool
    parent_id: Optional[str] = None
    created_at: datetime
    reactions: list[ReactionOut] = []
    reply_count: int = 0

    model_config = {"from_attributes": True}


class MessagesPageOut(BaseModel):
    messages: list[MessageOut]
    next_cursor: Optional[str] = None


class SendMessageIn(BaseModel):
    content: str
    parent_id: Optional[str] = None


class AddReactionIn(BaseModel):
    emoji: str
