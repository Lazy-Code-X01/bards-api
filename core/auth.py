from fastapi import Header, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_session


async def get_current_user(
    x_user_id: str = Header(...),
    session: AsyncSession = Depends(get_session),
):
    from models.user import User

    user = await session.get(User, x_user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{x_user_id}' not found")
    return user
