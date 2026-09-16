from decimal import Decimal
from urllib.parse import parse_qs, urlparse

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings
from database.models import CartItem, OrderStatus
from middleware import is_admin
from services.cart_service import CartService
from services.exceptions import EmptyCart, InsufficientStock
from services.favorite_service import FavoriteService
from services.order_service import OrderService
from utils.deep_links import manager_deep_link, order_message


@pytest.mark.asyncio
async def test_cart_total_and_stock(session: AsyncSession, catalog: tuple) -> None:
    user, product = catalog
    service = CartService(session)
    await service.add(user.id, product.id, 2)
    items = await service.items(user.id)
    assert service.total(items) == Decimal("3000")
    with pytest.raises(InsufficientStock) as error:
        await service.add(user.id, product.id, 2)
    assert error.value.available == 3


@pytest.mark.asyncio
async def test_cart_quantity_and_remove(session: AsyncSession, catalog: tuple) -> None:
    user, product = catalog
    service = CartService(session)
    await service.add(user.id, product.id)
    await service.set_quantity(user.id, product.id, 3)
    assert (await service.items(user.id))[0].quantity == 3
    await service.set_quantity(user.id, product.id, 0)
    assert await service.items(user.id) == []


@pytest.mark.asyncio
async def test_favorite_toggle(session: AsyncSession, catalog: tuple) -> None:
    user, product = catalog
    service = FavoriteService(session)
    assert await service.toggle(user.id, product.id) is True
    assert await service.ids(user.id) == [product.id]
    assert await service.toggle(user.id, product.id) is False
    assert await service.ids(user.id) == []


@pytest.mark.asyncio
async def test_order_snapshots_and_decrements_stock(session: AsyncSession, catalog: tuple) -> None:
    user, product = catalog
    await CartService(session).add(user.id, product.id, 2)
    order = await OrderService(session).create_from_cart(user.id)
    assert order.total_amount == Decimal("3000")
    assert product.stock == 1
    assert order.items[0].product_name == "Товар"
    assert order.items[0].price == Decimal("1500")
    assert await session.scalar(select(CartItem.id).where(CartItem.user_id == user.id)) is None
    with pytest.raises(EmptyCart):
        await OrderService(session).create_from_cart(user.id)


@pytest.mark.asyncio
async def test_order_status_transitions(session: AsyncSession, catalog: tuple) -> None:
    user, product = catalog
    await CartService(session).add(user.id, product.id)
    order = await OrderService(session).create_from_cart(user.id)
    await OrderService(session).change_status(order.id, OrderStatus.ACCEPTED)
    await OrderService(session).change_status(order.id, OrderStatus.COMPLETED)
    with pytest.raises(ValueError):
        await OrderService(session).change_status(order.id, OrderStatus.NEW)


@pytest.mark.asyncio
async def test_deep_link_encodes_unicode(session: AsyncSession, catalog: tuple) -> None:
    user, product = catalog
    await CartService(session).add(user.id, product.id)
    order = await OrderService(session).create_from_cart(user.id)
    text = order_message(order)
    link = manager_deep_link("manager_one", text)
    parsed = urlparse(link)
    assert parsed.netloc == "t.me"
    assert parsed.path == "/manager_one"
    assert parse_qs(parsed.query)["text"] == [text]
    assert "%F0%9F%9B%92" in link
    assert "%E2%82%BD" in link


def test_admin_rights() -> None:
    settings = Settings(admin_ids="11,22", order_manager_usernames="manager")
    assert is_admin(11, settings)
    assert not is_admin(33, settings)
