from collections.abc import AsyncIterator
from decimal import Decimal

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from database.database import Database
from database.models import Category, Product, User


@pytest_asyncio.fixture
async def session(tmp_path: object) -> AsyncIterator[AsyncSession]:
    database = Database(f"sqlite+aiosqlite:///{tmp_path}/test.db")
    await database.create_schema()
    async with database.session_factory() as value:
        yield value
        await value.rollback()
    await database.close()


@pytest_asyncio.fixture
async def catalog(session: AsyncSession) -> tuple[User, Product]:
    category = Category(name="Тест")
    user = User(telegram_id=100, first_name="Иван")
    product = Product(name="Товар", short_description="Кратко", description="Описание", characteristics="Цвет: чёрный",
                      price=Decimal("1500"), article="ABC-123", stock=3, category=category)
    session.add_all((category, user, product))
    await session.flush()
    return user, product
