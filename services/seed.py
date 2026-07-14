from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.channel import Channel, ChannelMember
from models.organization import Organization
from models.user import User

ORGANIZATIONS = [
    {"id": "org-alpha", "name": "Alpha Corp"},
    {"id": "org-beta", "name": "Beta Corp"},
]

USERS = [
    {"id": "u1", "organization_id": "org-alpha", "name": "Adaeze Okonkwo", "avatar": "AO", "role": "Product Lead", "email": "adaeze@obaplatforms.com"},
    {"id": "u2", "organization_id": "org-alpha", "name": "Kofi Mensah", "avatar": "KM", "role": "Engineer", "email": "kofi@obaplatforms.com"},
    {"id": "u3", "organization_id": "org-alpha", "name": "Fatima Al-Hassan", "avatar": "FA", "role": "Designer", "email": "fatima@obaplatforms.com"},
    {"id": "u4", "organization_id": "org-alpha", "name": "Olu Adeyemi", "avatar": "OA", "role": "Admin", "email": "olu@obaplatforms.com"},
    {"id": "u5", "organization_id": "org-alpha", "name": "Kingdom Bot", "avatar": "KB", "role": "bot", "email": "bot@obaplatforms.com"},
    {"id": "demo-org-a", "organization_id": "org-alpha", "name": "Demo Alpha", "avatar": "DA", "role": "member", "email": "demo-a@obaplatforms.com"},
    {"id": "demo-org-b", "organization_id": "org-beta", "name": "Demo Beta", "avatar": "DB", "role": "member", "email": "demo-b@obaplatforms.com"},
    {"id": "u6", "organization_id": "org-beta", "name": "Beta Bot", "avatar": "BB", "role": "bot", "email": "bot@betacorp.com"},
]

CHANNELS = [
    {"id": "alpha-system-alerts", "organization_id": "org-alpha", "name": "system-alerts", "type": "system", "description": "System-wide alerts", "icon": "solar:bell-bold", "icon_color": "orange.400"},
    {"id": "alpha-envoy-updates", "organization_id": "org-alpha", "name": "envoy-updates", "type": "system", "description": "Envoy agent updates", "icon": "solar:robot-bold", "icon_color": "purple.400"},
    {"id": "alpha-charm-deployments", "organization_id": "org-alpha", "name": "charm-deployments", "type": "system", "description": "Charm deployment events", "icon": "solar:settings-bold", "icon_color": "blue.400"},
    {"id": "alpha-court-updates", "organization_id": "org-alpha", "name": "court-updates", "type": "system", "description": "Court updates", "icon": "solar:crown-bold", "icon_color": "green.400"},
    {"id": "alpha-lead-qualifier", "organization_id": "org-alpha", "name": "envoy-lead-qualifier", "type": "envoy", "description": "Lead qualification agent"},
    {"id": "alpha-market-scout", "organization_id": "org-alpha", "name": "envoy-market-scout", "type": "envoy", "description": "Market scouting agent"},
    {"id": "alpha-general", "organization_id": "org-alpha", "name": "general", "type": "team", "description": "General discussion"},
    {"id": "alpha-agents-alerts", "organization_id": "org-alpha", "name": "agents-alerts", "type": "team", "description": "Agent alerts"},
    {"id": "alpha-reports", "organization_id": "org-alpha", "name": "reports", "type": "team", "description": "Reports"},
    {"id": "alpha-dm-adaeze", "organization_id": "org-alpha", "name": "adaeze", "type": "dm", "description": ""},
    {"id": "alpha-dm-kofi", "organization_id": "org-alpha", "name": "kofi", "type": "dm", "description": ""},
    {"id": "alpha-dm-bot", "organization_id": "org-alpha", "name": "Kingdom Bot", "type": "dm", "description": ""},
    {"id": "beta-system-alerts", "organization_id": "org-beta", "name": "system-alerts", "type": "system", "description": "System-wide alerts", "icon": "solar:bell-bold", "icon_color": "orange.400"},
    {"id": "beta-general", "organization_id": "org-beta", "name": "general", "type": "team", "description": "General discussion"},
    {"id": "beta-dm-bot", "organization_id": "org-beta", "name": "Beta Bot", "type": "dm", "description": ""},
]

ALPHA = ["u1", "u2", "u3", "u4", "u5", "demo-org-a"]
BETA = ["demo-org-b", "u6"]

CHANNEL_MEMBERS: dict[str, list[str]] = {
    "alpha-system-alerts": ALPHA,
    "alpha-envoy-updates": ALPHA,
    "alpha-charm-deployments": ALPHA,
    "alpha-court-updates": ALPHA,
    "alpha-lead-qualifier": ALPHA,
    "alpha-market-scout": ALPHA,
    "alpha-general": ALPHA,
    "alpha-agents-alerts": ALPHA,
    "alpha-reports": ALPHA,
    "alpha-dm-adaeze": ["demo-org-a", "u1"],
    "alpha-dm-kofi": ["demo-org-a", "u2"],
    "alpha-dm-bot": ["demo-org-a", "u5"],
    "beta-system-alerts": BETA,
    "beta-general": BETA,
    "beta-dm-bot": ["demo-org-b", "u6"],
}


async def seed_if_empty(session: AsyncSession) -> bool:
    count = await session.scalar(select(func.count(User.id)))
    if count and count > 0:
        return False

    for org in ORGANIZATIONS:
        session.add(Organization(**org))
    await session.flush()

    for u in USERS:
        session.add(User(**u, online=False))

    for ch in CHANNELS:
        session.add(Channel(**ch))
    await session.flush()

    for channel_id, user_ids in CHANNEL_MEMBERS.items():
        for user_id in user_ids:
            session.add(ChannelMember(channel_id=channel_id, user_id=user_id))

    await session.commit()
    return True
