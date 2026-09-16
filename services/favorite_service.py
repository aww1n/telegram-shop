from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AnalyticsEvent, EventType, Favorite, Product
from services.exceptions import ProductUnavailable


class FavoriteService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def toggle(self, user_id: int, product_id: int) -> bool:
        product = await self.session.get(Product, product_id)
        if product is None:
            raise ProductUnavailable("Товар больше недоступен.")
        favorite = await self.session.scalar(select(Favorite).where(Favorite.user_id == user_id, Favorite.product_id == product_id))
        if favorite:
            await self.session.delete(favorite)
            event = EventType.FAVORITE_REMOVE
            enabled = False
        else:
            self.session.add(Favorite(user_id=user_id, product_id=product_id))
            event = EventType.FAVORITE_ADD
            enabled = True
        self.session.add(AnalyticsEvent(user_id=user_id, product_id=product_id, event_type=event))
        return enabled

    async def ids(self, user_id: int) -> list[int]:
        return list((await self.session.scalars(select(Favorite.product_id).where(Favorite.user_id == user_id).order_by(Favorite.created_at.desc()))).all())
