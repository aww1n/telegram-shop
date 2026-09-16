import math

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.catalog import CatalogRepository
from handlers.user.common import edit
from keyboards.product import product_list
from keyboards.user import back_home
from states.user import SearchState

router = Router(name="user_search")


@router.callback_query(F.data == "search")
async def search_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SearchState.query)
    await edit(callback, "🔎 Введите название, артикул, описание или характеристику товара:", back_home())
    await callback.answer()


@router.message(SearchState.query)
async def search_result(message: Message, state: FSMContext, session: AsyncSession) -> None:
    text = (message.text or "").strip()
    await state.clear()
    if len(text) < 2:
        await message.answer("Введите не менее двух символов.", reply_markup=back_home())
        return
    products, total = await CatalogRepository(session).products(query_text=text, page_size=10)
    if not products:
        await message.answer("🔎 Ничего не найдено.\n\nПопробуйте изменить запрос.", reply_markup=back_home())
        return
    await message.answer(f"🔎 Найдено: {total}", reply_markup=product_list(products, 1, max(1, math.ceil(total / 10))))
