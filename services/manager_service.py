from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Manager


class ManagerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def sync(self, usernames: tuple[str, ...]) -> None:
        if usernames:
            await self.session.execute(update(Manager).where(Manager.username.not_in(usernames)).values(is_active=False))
        for username in usernames:
            existing = await self.session.scalar(select(Manager).where(Manager.username == username))
            if existing is None:
                self.session.add(Manager(username=username, name=username))
            else:
                existing.is_active = True

    async def primary_username(self, configured: tuple[str, ...]) -> str:
        manager = await self.session.scalar(select(Manager).where(Manager.is_active.is_(True)).order_by(Manager.id))
        if manager:
            return manager.username
        if configured:
            return configured[0]
        raise ValueError("Нет активного менеджера")
