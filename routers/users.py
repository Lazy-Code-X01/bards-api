from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user
from core.database import get_session
from models.user import User
from schemas.user import UserOut

router = APIRouter(prefix="/users", tags=["users"])


class PresenceIn(BaseModel):
    online: bool


@router.get("", response_model=list[UserOut])
async def list_users(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    rows = (await session.execute(
        select(User)
        .where(User.organization_id == current_user.organization_id)
        .order_by(User.name)
    )).scalars().all()
    return rows


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me/presence", response_model=UserOut)
async def update_presence(
    body: PresenceIn,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    current_user.online = body.online
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user
