from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AnalyticsEvent, EventType, Order, Product, User


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(self, event_type: EventType, user_id: int | None = None, product_id: int | None = None) -> None:
        self.session.add(AnalyticsEvent(event_type=event_type, user_id=user_id, product_id=product_id))

    async def summary(self, since: datetime | None = None) -> dict[str, int | str]:
        event_filter = AnalyticsEvent.created_at >= since if since else True
        order_filter = Order.created_at >= since if since else True
        user_filter = User.created_at >= since if since else True
        values: dict[str, int | str] = {}
        values["users"] = int(await self.session.scalar(select(func.count(User.id)).where(user_filter)) or 0)
        for event in EventType:
            values[event.value] = int(await self.session.scalar(select(func.count(AnalyticsEvent.id)).where(event_filter, AnalyticsEvent.event_type == event)) or 0)
        values["orders"] = int(await self.session.scalar(select(func.count(Order.id)).where(order_filter)) or 0)
        values["revenue"] = str(await self.session.scalar(select(func.coalesce(func.sum(Order.total_amount), 0)).where(order_filter)) or 0)
        values["products"] = int(await self.session.scalar(select(func.count(Product.id))) or 0)
        values["out_of_stock"] = int(await self.session.scalar(select(func.count(Product.id)).where(Product.stock <= 0)) or 0)
        return values
