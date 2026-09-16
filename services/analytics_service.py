from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.analytics import AnalyticsRepository


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = AnalyticsRepository(session)

    async def for_days(self, days: int | None) -> dict[str, int | str]:
        since = datetime.now(timezone.utc) - timedelta(days=days) if days else None
        return await self.repository.summary(since)
