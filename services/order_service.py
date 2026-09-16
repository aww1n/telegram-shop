from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import AnalyticsEvent, CartItem, EventType, Order, OrderItem, OrderStatus, Product
from services.exceptions import EmptyCart, InsufficientStock, ProductUnavailable


ALLOWED_TRANSITIONS = {
    OrderStatus.NEW: {OrderStatus.PROCESSING, OrderStatus.ACCEPTED, OrderStatus.CANCELLED, OrderStatus.REJECTED},
    OrderStatus.PROCESSING: {OrderStatus.ACCEPTED, OrderStatus.CANCELLED, OrderStatus.REJECTED},
    OrderStatus.ACCEPTED: {OrderStatus.COMPLETED, OrderStatus.CANCELLED},
    OrderStatus.COMPLETED: set(), OrderStatus.CANCELLED: set(), OrderStatus.REJECTED: set(),
}


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_from_cart(self, user_id: int) -> Order:
        query = select(CartItem).where(CartItem.user_id == user_id).options(selectinload(CartItem.product)).order_by(CartItem.id)
        cart = list((await self.session.scalars(query)).all())
        if not cart:
            raise EmptyCart("Корзина пуста.")
        total = Decimal("0")
        order = Order(user_id=user_id, total_amount=0, status=OrderStatus.NEW, items=[])
        self.session.add(order)
        for cart_item in cart:
            product = await self.session.scalar(select(Product).where(Product.id == cart_item.product_id).with_for_update())
            if product is None or not product.is_active:
                raise ProductUnavailable(f"Товар «{cart_item.product.name}» недоступен.")
            if cart_item.quantity > product.stock:
                raise InsufficientStock(product.stock)
            line_total = product.price * cart_item.quantity
            total += line_total
            product.stock -= cart_item.quantity
            order.items.append(OrderItem(product_id=product.id, product_name=product.name, article=product.article,
                                         price=product.price, quantity=cart_item.quantity, total=line_total))
        order.total_amount = total
        self.session.add(AnalyticsEvent(user_id=user_id, event_type=EventType.ORDER_CREATED))
        await self.session.execute(delete(CartItem).where(CartItem.user_id == user_id))
        await self.session.flush()
        return order

    async def history(self, user_id: int) -> list[Order]:
        query = select(Order).where(Order.user_id == user_id).options(selectinload(Order.items)).order_by(Order.created_at.desc())
        return list((await self.session.scalars(query)).all())

    async def change_status(self, order_id: int, status: OrderStatus) -> Order:
        order = await self.session.get(Order, order_id)
        if order is None:
            raise ValueError("Заказ не найден")
        if status not in ALLOWED_TRANSITIONS[order.status]:
            raise ValueError(f"Недопустимый переход {order.status.value} → {status.value}")
        order.status = status
        return order
