from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Product
from handlers.user.common import current_user, edit
from keyboards.product import product_list
from services.favorite_service import FavoriteService

router = Router(name="user_favorites")


@router.callback_query(F.data.startswith("fav:toggle:"))
async def toggle(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await current_user(callback, session)
    enabled = await FavoriteService(session).toggle(user.id, int(callback.data.rsplit(":", 1)[1]))
    await callback.answer("Добавлено в избранное" if enabled else "Удалено из избранного")


@router.callback_query(F.data == "favorites")
async def favorites(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await current_user(callback, session)
    ids = await FavoriteService(session).ids(user.id)
    products = list((await session.scalars(select(Product).where(Product.id.in_(ids)).order_by(Product.name))).all()) if ids else []
    await edit(callback, "❤️ <b>Избранное</b>" if products else "В избранном пока ничего нет.", product_list(products, 1, 1))
    await callback.answer()
