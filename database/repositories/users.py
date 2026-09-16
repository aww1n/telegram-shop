from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(self, telegram_id: int, username: str | None, first_name: str, last_name: str | None) -> tuple[User, bool]:
        user = await self.session.scalar(select(User).where(User.telegram_id == telegram_id))
        created = user is None
        if user is None:
            user = User(telegram_id=telegram_id, username=username, first_name=first_name, last_name=last_name)
            self.session.add(user)
        else:
            user.username, user.first_name, user.last_name = username, first_name, last_name
            user.last_active_at = datetime.now(timezone.utc)
        await self.session.flush()
        return user, created

    async def by_telegram_id(self, telegram_id: int) -> User | None:
        return await self.session.scalar(select(User).where(User.telegram_id == telegram_id))
