from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import AnalyticsEvent, CartItem, EventType, Product
from services.exceptions import InsufficientStock, ProductUnavailable


class CartService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def items(self, user_id: int) -> list[CartItem]:
        query = select(CartItem).where(CartItem.user_id == user_id).options(selectinload(CartItem.product)).order_by(CartItem.id)
        return list((await self.session.scalars(query)).all())

    async def add(self, user_id: int, product_id: int, quantity: int = 1) -> CartItem:
        if quantity < 1:
            raise ValueError("quantity must be positive")
        product = await self.session.get(Product, product_id)
        if product is None or not product.is_active:
            raise ProductUnavailable("Товар больше недоступен.")
        item = await self.session.scalar(select(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id))
        requested = quantity + (item.quantity if item else 0)
        if requested > product.stock:
            raise InsufficientStock(product.stock)
        if item is None:
            item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
            self.session.add(item)
        else:
            item.quantity = requested
        self.session.add(AnalyticsEvent(user_id=user_id, product_id=product_id, event_type=EventType.CART_ADD))
        await self.session.flush()
        return item

    async def set_quantity(self, user_id: int, product_id: int, quantity: int) -> None:
        item = await self.session.scalar(select(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id))
        if item is None:
            raise ProductUnavailable("Товара нет в корзине.")
        if quantity <= 0:
            await self.remove(user_id, product_id)
            return
        product = await self.session.get(Product, product_id)
        if product is None or quantity > product.stock:
            raise InsufficientStock(product.stock if product else 0)
        item.quantity = quantity

    async def remove(self, user_id: int, product_id: int) -> None:
        await self.session.execute(delete(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id))
        self.session.add(AnalyticsEvent(user_id=user_id, product_id=product_id, event_type=EventType.CART_REMOVE))

    async def clear(self, user_id: int) -> None:
        await self.session.execute(delete(CartItem).where(CartItem.user_id == user_id))

    @staticmethod
    def total(items: list[CartItem]) -> Decimal:
        return sum((item.product.price * item.quantity for item in items), Decimal("0"))
