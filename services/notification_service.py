from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import NotificationPreference, User


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def set_preference(self, user_id: int, kind: str, enabled: bool) -> None:
        preference = await self.session.scalar(select(NotificationPreference).where(NotificationPreference.user_id == user_id, NotificationPreference.kind == kind))
        if preference is None:
            self.session.add(NotificationPreference(user_id=user_id, kind=kind, enabled=enabled))
        else:
            preference.enabled = enabled

    async def send(self, bot: Bot, user: User, kind: str, text: str) -> bool:
        preference = await self.session.scalar(select(NotificationPreference).where(NotificationPreference.user_id == user.id, NotificationPreference.kind == kind))
        if preference and not preference.enabled:
            return False
        await bot.send_message(user.telegram_id, text)
        return True
