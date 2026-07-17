from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user
from core.database import get_session
from models.notification import Notification
from models.user import User
from schemas.notification import NotificationsPageOut, NotificationOut, UnreadCountOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationsPageOut)
async def list_notifications(
    cursor: str | None = Query(None),
    limit: int = Query(50, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    q = select(Notification).where(
        and_(
            Notification.user_id == current_user.id,
            Notification.organization_id == current_user.organization_id,
        )
    )
    if cursor:
        q = q.where(Notification.created_at < datetime.fromisoformat(cursor))

    q = q.order_by(Notification.created_at.desc()).limit(limit)
    rows = (await session.execute(q)).scalars().all()

    next_cursor = rows[-1].created_at.isoformat() if len(rows) == limit else None
    return NotificationsPageOut(notifications=rows, next_cursor=next_cursor)


@router.get("/unread-count", response_model=UnreadCountOut)
async def unread_count(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    count = await session.scalar(
        select(func.count(Notification.id)).where(
            and_(
                Notification.user_id == current_user.id,
                Notification.organization_id == current_user.organization_id,
                Notification.read == False,
            )
        )
    )
    return UnreadCountOut(count=count or 0)


@router.patch("/read-all", status_code=204)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    rows = (await session.execute(
        select(Notification).where(
            and_(
                Notification.user_id == current_user.id,
                Notification.organization_id == current_user.organization_id,
                Notification.read == False,
            )
        )
    )).scalars().all()

    for notif in rows:
        notif.read = True
    await session.commit()


@router.patch("/{notification_id}/read", response_model=NotificationOut)
async def mark_one_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    notif = await session.get(Notification, notification_id)
    if not notif or notif.user_id != current_user.id or notif.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.read = True
    await session.commit()
    await session.refresh(notif)
    return notif
