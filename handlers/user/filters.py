import math

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.catalog import CatalogRepository
from handlers.user.common import edit
from keyboards.product import product_list
from states.user import FilterState
from utils.validators import positive_decimal

router = Router(name="user_filters")


@router.callback_query(F.data == "filters")
async def filters_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(FilterState.min_price)
    await edit(callback, "🔎 <b>Фильтры</b>\n\nВведите минимальную цену или 0:")
    await callback.answer()


@router.message(FilterState.min_price)
async def minimum(message: Message, state: FSMContext) -> None:
    try:
        value = positive_decimal(message.text or "")
    except ValueError as error:
        await message.answer(str(error))
        return
    await state.update_data(min_price=str(value))
    await state.set_state(FilterState.max_price)
    await message.answer("Введите максимальную цену или 0, если верхней границы нет:")


@router.message(FilterState.max_price)
async def maximum(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        maximum_value = positive_decimal(message.text or "")
    except ValueError as error:
        await message.answer(str(error))
        return
    data = await state.get_data()
    minimum_value = positive_decimal(data["min_price"])
    if maximum_value and maximum_value < minimum_value:
        await message.answer("Максимальная цена должна быть не меньше минимальной.")
        return
    await state.clear()
    products, total = await CatalogRepository(session).products(
        min_price=minimum_value, max_price=maximum_value or None, in_stock=True, page_size=10,
    )
    if not products:
        await message.answer("По выбранным фильтрам ничего не найдено.")
        return
    await message.answer(
        f"🔎 Найдено: {total}\nПоказаны товары в наличии от {minimum_value:g} до {maximum_value:g} ₽.",
        reply_markup=product_list(products, 1, max(1, math.ceil(total / 10))),
    )
