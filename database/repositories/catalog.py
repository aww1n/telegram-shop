from decimal import Decimal

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import AnalyticsEvent, Category, Product


class CatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _active(self) -> Select[tuple[Product]]:
        return select(Product).where(Product.is_active.is_(True)).options(selectinload(Product.category), selectinload(Product.photos))

    async def product(self, product_id: int, include_hidden: bool = False) -> Product | None:
        query = select(Product).where(Product.id == product_id).options(selectinload(Product.category), selectinload(Product.photos))
        if not include_hidden:
            query = query.where(Product.is_active.is_(True))
        return await self.session.scalar(query)

    async def categories(self, include_hidden: bool = False) -> list[Category]:
        query = select(Category).order_by(Category.name)
        if not include_hidden:
            query = query.where(Category.is_active.is_(True))
        return list((await self.session.scalars(query)).all())

    async def products(self, *, page: int = 1, page_size: int = 6, category_id: int | None = None,
                       query_text: str | None = None, min_price: Decimal | None = None,
                       max_price: Decimal | None = None, in_stock: bool = False,
                       sort: str = "new") -> tuple[list[Product], int]:
        query = self._active()
        if category_id:
            query = query.where(Product.category_id == category_id)
        if query_text:
            pattern = f"%{query_text.strip()}%"
            query = query.where(or_(Product.name.ilike(pattern), Product.article.ilike(pattern),
                                    Product.description.ilike(pattern), Product.characteristics.ilike(pattern)))
        if min_price is not None:
            query = query.where(Product.price >= min_price)
        if max_price is not None:
            query = query.where(Product.price <= max_price)
        if in_stock:
            query = query.where(Product.stock > 0)
        count_query = select(func.count()).select_from(query.order_by(None).subquery())
        total = int(await self.session.scalar(count_query) or 0)
        popularity = select(func.count(AnalyticsEvent.id)).where(AnalyticsEvent.product_id == Product.id).correlate(Product).scalar_subquery()
        ordering = {"cheap": Product.price.asc(), "expensive": Product.price.desc(), "new": Product.created_at.desc(), "popular": popularity.desc()}
        query = query.order_by(ordering.get(sort, Product.created_at.desc())).offset((page - 1) * page_size).limit(page_size)
        return list((await self.session.scalars(query)).unique().all()), total
