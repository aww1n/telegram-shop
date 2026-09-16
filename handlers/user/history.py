from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings
from handlers.user.common import current_user, edit
from keyboards.product import product_list
from services.product_service import ProductService

router = Router(name="user_history")


@router.callback_query(F.data == "recent")
async def recent(callback: CallbackQuery, session: AsyncSession, settings: Settings) -> None:
    user = await current_user(callback, session)
    products = await ProductService(session, settings.recently_viewed_limit).recent_products(user.id)
    await edit(callback, "🕘 <b>Недавно просмотренные</b>" if products else "Вы ещё не просматривали товары.", product_list(products, 1, 1))
    await callback.answer()
