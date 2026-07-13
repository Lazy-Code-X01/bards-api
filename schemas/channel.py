from pydantic import BaseModel
from typing import Optional


class ChannelOut(BaseModel):
    id: str
    name: str
    type: str
    description: str
    icon: Optional[str] = None
    icon_color: Optional[str] = None
    muted: bool
    unread: int = 0

    model_config = {"from_attributes": True}


class ChannelListOut(BaseModel):
    system: list[ChannelOut]
    team: list[ChannelOut]
    envoy: list[ChannelOut]
    dms: list[ChannelOut]
