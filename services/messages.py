from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.message import Message
from models.reaction import Reaction
from models.user import User
from schemas.message import MessageOut, ReactionOut


async def reactions_for(
    session: AsyncSession, message_id: str, user_id: str
) -> list[ReactionOut]:
    rows = await session.execute(
        select(Reaction.emoji, func.count(Reaction.id).label("count"))
        .where(Reaction.message_id == message_id)
        .group_by(Reaction.emoji)
    )
    user_rows = await session.execute(
        select(Reaction.emoji).where(
            and_(Reaction.message_id == message_id, Reaction.user_id == user_id)
        )
    )
    user_emojis = set(user_rows.scalars().all())
    return [ReactionOut(emoji=r.emoji, count=r.count, reacted=r.emoji in user_emojis) for r in rows]


async def build_message_out(
    msg: Message, session: AsyncSession, user_id: str
) -> MessageOut:
    sender = await session.get(User, msg.sender_id) if msg.sender_id else None
    msg_reactions = await reactions_for(session, msg.id, user_id)
    reply_count = await session.scalar(
        select(func.count(Message.id)).where(Message.parent_id == msg.id)
    ) or 0
    return MessageOut(
        id=msg.id,
        channel_id=msg.channel_id,
        sender=sender,
        content=msg.content,
        is_system=msg.is_system,
        is_agent=msg.is_agent,
        system_type=msg.system_type,
        system_action=msg.system_action,
        pinned=msg.pinned,
        parent_id=msg.parent_id,
        created_at=msg.created_at,
        reactions=msg_reactions,
        reply_count=reply_count,
    )
