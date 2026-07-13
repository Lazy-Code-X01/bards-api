import asyncio

import models  # noqa: F401
from core.database import AsyncSessionLocal, Base, engine
from models.channel import Channel, ChannelMember
from models.user import User

USERS = [
    {"id": "u1", "name": "Adaeze Okonkwo", "avatar": "AO", "role": "Product Lead", "email": "adaeze@obaplatforms.com"},
    {"id": "u2", "name": "Kofi Mensah", "avatar": "KM", "role": "Engineer", "email": "kofi@obaplatforms.com"},
    {"id": "u3", "name": "Fatima Al-Hassan", "avatar": "FA", "role": "Designer", "email": "fatima@obaplatforms.com"},
    {"id": "u4", "name": "Olu Adeyemi", "avatar": "OA", "role": "Admin", "email": "olu@obaplatforms.com"},
    {"id": "u5", "name": "Kingdom Bot", "avatar": "KB", "role": "bot", "email": "bot@obaplatforms.com"},
    {"id": "demo", "name": "Demo User", "avatar": "DU", "role": "member", "email": "demo@obaplatforms.com"},
]

CHANNELS = [
    {"id": "system-alerts", "name": "system-alerts", "type": "system", "description": "System-wide alerts", "icon": "solar:bell-bold", "icon_color": "orange.400"},
    {"id": "envoy-updates", "name": "envoy-updates", "type": "system", "description": "Envoy agent updates", "icon": "solar:robot-bold", "icon_color": "purple.400"},
    {"id": "charm-deployments", "name": "charm-deployments", "type": "system", "description": "Charm deployment events", "icon": "solar:settings-bold", "icon_color": "blue.400"},
    {"id": "court-updates", "name": "court-updates", "type": "system", "description": "Court updates", "icon": "solar:crown-bold", "icon_color": "green.400"},
    {"id": "envoy-lead-qualifier", "name": "envoy-lead-qualifier", "type": "envoy", "description": "Lead qualification agent"},
    {"id": "envoy-market-scout", "name": "envoy-market-scout", "type": "envoy", "description": "Market scouting agent"},
    {"id": "general", "name": "general", "type": "team", "description": "General discussion"},
    {"id": "agents-alerts", "name": "agents-alerts", "type": "team", "description": "Agent alerts"},
    {"id": "reports", "name": "reports", "type": "team", "description": "Reports"},
    {"id": "dm-adaeze", "name": "adaeze", "type": "dm", "description": ""},
    {"id": "dm-kofi", "name": "kofi", "type": "dm", "description": ""},
    {"id": "dm-bot", "name": "Kingdom Bot", "type": "dm", "description": ""},
]

ALL = [u["id"] for u in USERS]

CHANNEL_MEMBERS: dict[str, list[str]] = {
    "system-alerts": ALL,
    "envoy-updates": ALL,
    "charm-deployments": ALL,
    "court-updates": ALL,
    "envoy-lead-qualifier": ALL,
    "envoy-market-scout": ALL,
    "general": ALL,
    "agents-alerts": ALL,
    "reports": ALL,
    "dm-adaeze": ["demo", "u1"],
    "dm-kofi": ["demo", "u2"],
    "dm-bot": ["demo", "u5"],
}


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        for u in USERS:
            if not await session.get(User, u["id"]):
                session.add(User(**u, online=False))

        for ch in CHANNELS:
            if not await session.get(Channel, ch["id"]):
                session.add(Channel(**ch))

        await session.commit()

        for channel_id, user_ids in CHANNEL_MEMBERS.items():
            for user_id in user_ids:
                if not await session.get(ChannelMember, (channel_id, user_id)):
                    session.add(ChannelMember(channel_id=channel_id, user_id=user_id))

        await session.commit()

    print("Seeded users, channels, and memberships.")
    print("Demo user ID: 'demo'  --  send X-User-Id: demo on all requests")


asyncio.run(seed())
