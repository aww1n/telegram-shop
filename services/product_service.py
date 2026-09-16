from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AnalyticsEvent, EventType, Product, RecentlyViewed


class ProductService:
    def __init__(self, session: AsyncSession, recent_limit: int = 20) -> None:
        self.session, self.recent_limit = session, recent_limit

    async def viewed(self, user_id: int, product_id: int) -> None:
        recent = await self.session.scalar(select(RecentlyViewed).where(RecentlyViewed.user_id == user_id, RecentlyViewed.product_id == product_id))
        if recent:
            recent.viewed_at = datetime.now(timezone.utc)
        else:
            self.session.add(RecentlyViewed(user_id=user_id, product_id=product_id))
        self.session.add(AnalyticsEvent(user_id=user_id, product_id=product_id, event_type=EventType.VIEW))
        ids = list((await self.session.scalars(select(RecentlyViewed.id).where(RecentlyViewed.user_id == user_id).order_by(RecentlyViewed.viewed_at.desc()).offset(self.recent_limit))).all())
        if ids:
            await self.session.execute(delete(RecentlyViewed).where(RecentlyViewed.id.in_(ids)))

    async def recent_products(self, user_id: int) -> list[Product]:
        query = select(Product).join(RecentlyViewed).where(RecentlyViewed.user_id == user_id).order_by(RecentlyViewed.viewed_at.desc()).limit(self.recent_limit)
        return list((await self.session.scalars(query)).all())
