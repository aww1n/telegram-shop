from html import escape

import logging

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings
from database.models import Product
from handlers.user.common import current_user, edit
from keyboards.user import back_home
from services.exceptions import ShopError
from services.manager_service import ManagerService
from services.order_service import OrderService
from utils.deep_links import manager_deep_link, order_message
from utils.formatting import STATUS_NAMES, money

router = Router(name="user_orders")
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery, session: AsyncSession, settings: Settings, admin_notification_bot: Bot) -> None:
    user = await current_user(callback, session)
    try:
        order = await OrderService(session).create_from_cart(user.id)
        manager = await ManagerService(session).primary_username(settings.manager_usernames)
        link = manager_deep_link(manager, order_message(order))
        await session.commit()
    except (ShopError, ValueError) as error:
        await callback.answer(str(error), show_alert=True)
        return
    try:
        low_stock = []
        for item in order.items:
            product = await session.get(Product, item.product_id) if item.product_id else None
            if product and product.stock <= settings.low_stock_threshold:
                low_stock.append(item)
        notice = f"📨 Новый заказ #{order.id}\nСумма: {money(order.total_amount)}"
        if low_stock:
            notice += "\n\n⚠️ Мало товара:\n" + "\n".join(f"{item.product_name}" for item in low_stock)
        for admin_id in settings.admin_id_values:
            await admin_notification_bot.send_message(admin_id, notice)
    except Exception:
        logger.exception("Unable to notify administrators about order %s", order.id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать менеджеру", url=link)],
        [InlineKeyboardButton(text="📦 Мои заказы", callback_data="orders")],
        [InlineKeyboardButton(text="◀️ Вернуться в корзину", callback_data="cart")],
    ])
    await edit(callback, "📨 <b>Заказ готов!</b>\n\nНажмите кнопку ниже — откроется чат с менеджером, а сообщение с заказом уже будет подготовлено.\n\nВам останется нажать «Отправить».", keyboard)
    await callback.answer()


@router.callback_query(F.data == "orders")
async def orders(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await current_user(callback, session)
    history = await OrderService(session).history(user.id)
    if not history:
        await edit(callback, "У вас пока нет заказов.", back_home())
        await callback.answer()
        return
    rows = [[InlineKeyboardButton(text=f"#{order.id} · {money(order.total_amount)} · {STATUS_NAMES[order.status]}", callback_data=f"order:{order.id}")] for order in history[:20]]
    rows.append([InlineKeyboardButton(text="◀️ Меню", callback_data="home")])
    await edit(callback, "📦 <b>Мои заказы</b>", InlineKeyboardMarkup(inline_keyboard=rows))
    await callback.answer()


@router.callback_query(F.data.regexp(r"^order:\d+$"))
async def order_detail(callback: CallbackQuery, session: AsyncSession, settings: Settings) -> None:
    user = await current_user(callback, session)
    history = await OrderService(session).history(user.id)
    order_id = int(callback.data.split(":")[1])
    order = next((item for item in history if item.id == order_id), None)
    if order is None:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    lines = [f"📦 <b>ЗАКАЗ #{order.id}</b>", ""]
    lines.extend(f"• {escape(item.product_name)} × {item.quantity} — {money(item.total)}" for item in order.items)
    lines.extend(("", f"💰 Итого: {money(order.total_amount)}", f"Статус: {STATUS_NAMES[order.status]}", f"Дата: {order.created_at:%d.%m.%Y %H:%M}"))
    manager = await ManagerService(session).primary_username(settings.manager_usernames)
    link = manager_deep_link(manager, order_message(order))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать менеджеру", url=link)],
        [InlineKeyboardButton(text="◀️ К заказам", callback_data="orders")],
    ])
    await edit(callback, "\n".join(lines), keyboard)
    await callback.answer()
