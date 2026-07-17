from fastapi import Header, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_session

_INVALID_PAIR = "Invalid user/organization pair"


async def get_current_user(
    x_user_id: str = Header(...),
    x_organization_id: str = Header(...),
    session: AsyncSession = Depends(get_session),
):
    from models.user import User

    user = await session.get(User, x_user_id)
    if not user or user.organization_id != x_organization_id:
        raise HTTPException(status_code=403, detail=_INVALID_PAIR)
    return user
