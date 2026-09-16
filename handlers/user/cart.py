from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.user.common import current_user, edit
from keyboards.cart import cart_keyboard
from services.cart_service import CartService
from services.exceptions import ShopError
from utils.formatting import money

router = Router(name="user_cart")


async def render(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await current_user(callback, session)
    service = CartService(session)
    items = await service.items(user.id)
    lines = ["🛒 <b>МОЯ КОРЗИНА</b>", ""]
    for item in items:
        lines.extend((f"📦 {escape(item.product.name)} × {item.quantity}", money(item.product.price * item.quantity), ""))
    lines.extend(("━━━━━━━━━━━━", f"💰 Итого: {money(service.total(items))}"))
    if not items:
        lines = ["🛒 Корзина пуста."]
    await edit(callback, "\n".join(lines), cart_keyboard(items))


@router.callback_query(F.data == "cart")
async def show_cart(callback: CallbackQuery, session: AsyncSession) -> None:
    await render(callback, session)
    await callback.answer()


@router.callback_query(F.data.startswith("cart:add:"))
async def add(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await current_user(callback, session)
    try:
        await CartService(session).add(user.id, int(callback.data.rsplit(":", 1)[1]))
        await callback.answer("Добавлено в корзину")
    except ShopError as error:
        await callback.answer(str(error), show_alert=True)


@router.callback_query(F.data.startswith("cart:inc:") | F.data.startswith("cart:dec:"))
async def change(callback: CallbackQuery, session: AsyncSession) -> None:
    _, action, product_id = callback.data.split(":")
    user = await current_user(callback, session)
    service = CartService(session)
    item = next((entry for entry in await service.items(user.id) if entry.product_id == int(product_id)), None)
    if item:
        try:
            await service.set_quantity(user.id, item.product_id, item.quantity + (1 if action == "inc" else -1))
        except ShopError as error:
            await callback.answer(str(error), show_alert=True)
            return
    await render(callback, session)
    await callback.answer()


@router.callback_query(F.data.startswith("cart:remove:"))
async def remove(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await current_user(callback, session)
    await CartService(session).remove(user.id, int(callback.data.rsplit(":", 1)[1]))
    await render(callback, session)
    await callback.answer("Удалено")


@router.callback_query(F.data == "cart:clear:ask")
async def clear_ask(callback: CallbackQuery) -> None:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, очистить", callback_data="cart:clear:yes")],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="cart")],
    ])
    await edit(callback, "Очистить всю корзину?", keyboard)
    await callback.answer()


@router.callback_query(F.data == "cart:clear:yes")
async def clear(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await current_user(callback, session)
    await CartService(session).clear(user.id)
    await render(callback, session)
    await callback.answer("Корзина очищена")
