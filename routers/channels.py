import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user
from core.database import get_session
from models.channel import Channel, ChannelMember, ChannelRead
from models.message import Message
from models.user import User
from schemas.channel import ChannelListOut, ChannelOut
from schemas.message import MessageOut, MessagesPageOut, SendMessageIn
from schemas.user import UserOut
from services.messages import build_message_out
from services.notifications import dispatch_notifications
from services.realtime import manager

router = APIRouter(prefix="/channels", tags=["channels"])

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


async def _resolve_channel(
    session: AsyncSession, channel_id: str, user: User
) -> Channel:
    channel = await session.get(Channel, channel_id)
    if not channel or channel.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Channel not found")
    member = await session.get(ChannelMember, (channel_id, user.id))
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this channel")
    return channel


async def _unread_count(session: AsyncSession, channel_id: str, user_id: str) -> int:
    read_row = await session.get(ChannelRead, (channel_id, user_id))
    since = read_row.last_read_at if read_row else EPOCH
    count = await session.scalar(
        select(func.count(Message.id)).where(
            and_(
                Message.channel_id == channel_id,
                Message.created_at > since,
                Message.sender_id != user_id,
                Message.parent_id == None,
            )
        )
    )
    return count or 0


@router.get("", response_model=ChannelListOut)
async def list_channels(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Channel)
        .join(ChannelMember, Channel.id == ChannelMember.channel_id)
        .where(
            and_(
                ChannelMember.user_id == current_user.id,
                Channel.organization_id == current_user.organization_id,
            )
        )
        .order_by(Channel.name)
    )
    channels = result.scalars().all()

    grouped: dict[str, list[ChannelOut]] = {"system": [], "team": [], "envoy": [], "dm": []}
    for ch in channels:
        unread = await _unread_count(session, ch.id, current_user.id)
        grouped[ch.type].append(ChannelOut(
            id=ch.id,
            name=ch.name,
            type=ch.type,
            description=ch.description,
            icon=ch.icon,
            icon_color=ch.icon_color,
            muted=ch.muted,
            unread=unread,
        ))

    return ChannelListOut(
        system=grouped["system"],
        team=grouped["team"],
        envoy=grouped["envoy"],
        dms=grouped["dm"],
    )


@router.get("/{channel_id}/messages", response_model=MessagesPageOut)
async def get_messages(
    channel_id: str,
    cursor: str | None = Query(None),
    limit: int = Query(50, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _resolve_channel(session, channel_id, current_user)

    q = select(Message).where(
        and_(Message.channel_id == channel_id, Message.parent_id == None, Message.deleted == False)
    )
    if cursor:
        q = q.where(Message.created_at < datetime.fromisoformat(cursor))

    q = q.order_by(Message.created_at.desc()).limit(limit)
    rows = (await session.execute(q)).scalars().all()

    messages = [await build_message_out(msg, session, current_user.id) for msg in rows]
    messages.reverse()

    next_cursor = rows[-1].created_at.isoformat() if len(rows) == limit else None
    return MessagesPageOut(messages=messages, next_cursor=next_cursor)


@router.post("/{channel_id}/messages", response_model=MessageOut)
async def send_message(
    channel_id: str,
    body: SendMessageIn,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _resolve_channel(session, channel_id, current_user)

    msg = Message(
        id=str(uuid.uuid4()),
        channel_id=channel_id,
        sender_id=current_user.id,
        content=body.content,
        parent_id=body.parent_id,
    )
    session.add(msg)
    await session.commit()
    await session.refresh(msg)

    out = await build_message_out(msg, session, current_user.id)
    await manager.broadcast(channel_id, {
        "event": "message.new",
        "channel_id": channel_id,
        "data": out.model_dump(mode="json"),
    })
    background_tasks.add_task(
        dispatch_notifications,
        channel_id,
        current_user.id,
        msg.id,
        current_user.organization_id,
    )
    return out


@router.post("/{channel_id}/read", status_code=204)
async def mark_read(
    channel_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _resolve_channel(session, channel_id, current_user)

    now = datetime.now(timezone.utc)
    read_row = await session.get(ChannelRead, (channel_id, current_user.id))
    if read_row:
        read_row.last_read_at = now
    else:
        session.add(ChannelRead(channel_id=channel_id, user_id=current_user.id, last_read_at=now))
    await session.commit()


@router.get("/{channel_id}/members", response_model=list[UserOut])
async def get_members(
    channel_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _resolve_channel(session, channel_id, current_user)

    rows = (await session.execute(
        select(User)
        .join(ChannelMember, User.id == ChannelMember.user_id)
        .where(ChannelMember.channel_id == channel_id)
        .order_by(User.name)
    )).scalars().all()

    return rows


@router.get("/{channel_id}/pins", response_model=list[MessageOut])
async def get_pins(
    channel_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _resolve_channel(session, channel_id, current_user)

    rows = (await session.execute(
        select(Message)
        .where(and_(Message.channel_id == channel_id, Message.pinned == True, Message.deleted == False))
        .order_by(Message.pinned_at.desc())
    )).scalars().all()

    return [await build_message_out(msg, session, current_user.id) for msg in rows]
