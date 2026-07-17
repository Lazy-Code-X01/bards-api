import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from models.channel import Channel, ChannelMember
from models.notification import Notification
from services.realtime import manager

NOTIFICATION_NEW_MESSAGE = "new_message"


async def dispatch_notifications(
    channel_id: str,
    sender_id: str,
    message_id: str,
    organization_id: str,
):
    async with AsyncSessionLocal() as session:
        channel = await session.get(Channel, channel_id)
        if not channel or channel.muted:
            return

        members = (await session.execute(
            select(ChannelMember).where(
                ChannelMember.channel_id == channel_id,
                ChannelMember.user_id != sender_id,
            )
        )).scalars().all()

        for member in members:
            notif = Notification(
                id=str(uuid.uuid4()),
                user_id=member.user_id,
                organization_id=organization_id,
                type=NOTIFICATION_NEW_MESSAGE,
                source_message_id=message_id,
                channel_id=channel_id,
            )
            session.add(notif)

        await session.commit()

        for member in members:
            await manager.broadcast_to_user(member.user_id, {
                "event": "notification.new",
                "data": {
                    "type": NOTIFICATION_NEW_MESSAGE,
                    "channel_id": channel_id,
                    "source_message_id": message_id,
                },
            })
