import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user
from core.database import get_session
from models.message import Message
from models.reaction import Reaction
from models.user import User
from schemas.message import AddReactionIn, MessageOut, ReactionOut
from services.messages import build_message_out, reactions_for
from services.realtime import manager

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/{message_id}/reactions", response_model=list[ReactionOut])
async def toggle_reaction(
    message_id: str,
    body: AddReactionIn,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    msg = await session.get(Message, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    existing = (await session.execute(
        select(Reaction).where(
            and_(
                Reaction.message_id == message_id,
                Reaction.user_id == current_user.id,
                Reaction.emoji == body.emoji,
            )
        )
    )).scalar_one_or_none()

    if existing:
        await session.delete(existing)
    else:
        session.add(Reaction(
            id=str(uuid.uuid4()),
            message_id=message_id,
            user_id=current_user.id,
            emoji=body.emoji,
        ))
    await session.commit()

    updated = await reactions_for(session, message_id, current_user.id)
    await manager.broadcast(msg.channel_id, {
        "event": "message.reaction",
        "channel_id": msg.channel_id,
        "data": {"message_id": message_id, "reactions": [r.model_dump() for r in updated]},
    })
    return updated


@router.delete("/{message_id}/reactions/{emoji}", response_model=list[ReactionOut])
async def remove_reaction(
    message_id: str,
    emoji: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    existing = (await session.execute(
        select(Reaction).where(
            and_(
                Reaction.message_id == message_id,
                Reaction.user_id == current_user.id,
                Reaction.emoji == emoji,
            )
        )
    )).scalar_one_or_none()

    if existing:
        await session.delete(existing)
        await session.commit()

    return await reactions_for(session, message_id, current_user.id)


@router.get("/{message_id}/replies", response_model=list[MessageOut])
async def get_replies(
    message_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    rows = (await session.execute(
        select(Message)
        .where(and_(Message.parent_id == message_id, Message.deleted == False))
        .order_by(Message.created_at.asc())
    )).scalars().all()

    return [await build_message_out(msg, session, current_user.id) for msg in rows]


@router.delete("/{message_id}", status_code=204)
async def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    msg = await session.get(Message, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if msg.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete another user's message")

    msg.deleted = True
    await session.commit()


@router.patch("/{message_id}/pin", response_model=MessageOut)
async def toggle_pin(
    message_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    msg = await session.get(Message, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    msg.pinned = not msg.pinned
    msg.pinned_by = current_user.id if msg.pinned else None
    msg.pinned_at = datetime.now(timezone.utc) if msg.pinned else None
    await session.commit()
    await session.refresh(msg)

    return await build_message_out(msg, session, current_user.id)
