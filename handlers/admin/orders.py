from html import escape

import logging

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Manager, Order, OrderStatus, User
from handlers.admin.common import edit
from services.order_service import ALLOWED_TRANSITIONS, OrderService
from services.notification_service import NotificationService
from utils.formatting import STATUS_NAMES, money

router = Router(name="admin_orders")
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "adm:orders")
async def orders(callback: CallbackQuery, session: AsyncSession) -> None:
    await render_orders(callback, session, None)
    await callback.answer()


async def render_orders(callback: CallbackQuery, session: AsyncSession, status_filter: OrderStatus | None) -> None:
    query = select(Order).order_by(Order.created_at.desc()).limit(50)
    if status_filter:
        query = query.where(Order.status == status_filter)
    entries = list((await session.scalars(query)).all())
    rows = [[InlineKeyboardButton(text=f"#{item.id} · {STATUS_NAMES[item.status]} · {money(item.total_amount)}", callback_data=f"adm:order:{item.id}")] for item in entries]
    rows.append([InlineKeyboardButton(text="Все", callback_data="adm:orders"), InlineKeyboardButton(text="Новые", callback_data="adm:orders:new"), InlineKeyboardButton(text="В работе", callback_data="adm:orders:processing")])
    rows.append([InlineKeyboardButton(text="Принятые", callback_data="adm:orders:accepted"), InlineKeyboardButton(text="Завершённые", callback_data="adm:orders:completed")])
    rows.append([InlineKeyboardButton(text="Отменённые", callback_data="adm:orders:cancelled")])
    rows.append([InlineKeyboardButton(text="◀️ Админ-панель", callback_data="adm:home")])
    await edit(callback, "📋 <b>Заказы</b>" if entries else "Заказов пока нет.", InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data.regexp(r"^adm:orders:(new|processing|accepted|completed|cancelled|rejected)$"))
async def filtered_orders(callback: CallbackQuery, session: AsyncSession) -> None:
    await render_orders(callback, session, OrderStatus(callback.data.rsplit(":", 1)[1]))
    await callback.answer()


@router.callback_query(F.data.regexp(r"^adm:order:\d+$"))
async def detail(callback: CallbackQuery, session: AsyncSession) -> None:
    order_id = int(callback.data.rsplit(":", 1)[1])
    order = await session.scalar(select(Order).where(Order.id == order_id).options(selectinload(Order.items), selectinload(Order.user), selectinload(Order.manager)))
    if order is None:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    lines = [f"📦 <b>ЗАКАЗ #{order.id}</b>", "", f"👤 {escape(order.user.first_name)}", f"@{escape(order.user.username or 'без_username')}", ""]
    lines.extend(f"• {escape(item.product_name)} × {item.quantity}" for item in order.items)
    lines.extend(("", f"💰 Итого: {money(order.total_amount)}", f"Статус: {STATUS_NAMES[order.status]}", f"Менеджер: {escape(order.manager.name) if order.manager else 'Не назначен'}"))
    rows = [[InlineKeyboardButton(text=STATUS_NAMES[status], callback_data=f"adm:order:status:{order.id}:{status.value}")] for status in ALLOWED_TRANSITIONS[order.status]]
    rows.append([InlineKeyboardButton(text="👨‍💼 Назначить менеджера", callback_data=f"adm:order:manager:{order.id}")])
    rows.append([InlineKeyboardButton(text="◀️ Заказы", callback_data="adm:orders")])
    await edit(callback, "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows))
    await callback.answer()


@router.callback_query(F.data.startswith("adm:order:status:"))
async def status(callback: CallbackQuery, session: AsyncSession, user_notification_bot: Bot) -> None:
    _, _, _, order_id, status_value = callback.data.split(":")
    try:
        order = await OrderService(session).change_status(int(order_id), OrderStatus(status_value))
        user = await session.get(User, order.user_id)
        await session.commit()
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return
    if user:
        try:
            await NotificationService(session).send(user_notification_bot, user, "order_status", f"Статус заказа #{order.id} изменён: {STATUS_NAMES[order.status]}")
        except Exception:
            logger.exception("Unable to notify user about order %s status", order.id)
    await callback.answer("Статус изменён")
    await orders(callback, session)


@router.callback_query(F.data.startswith("adm:order:manager:"))
async def manager_choices(callback: CallbackQuery, session: AsyncSession) -> None:
    order_id = int(callback.data.rsplit(":", 1)[1])
    managers = list((await session.scalars(select(Manager).where(Manager.is_active.is_(True)).order_by(Manager.name))).all())
    rows = [[InlineKeyboardButton(text=f"@{manager.username}", callback_data=f"adm:assign:{order_id}:{manager.id}")] for manager in managers]
    rows.append([InlineKeyboardButton(text="◀️ К заказу", callback_data=f"adm:order:{order_id}")])
    await edit(callback, "Выберите менеджера:", InlineKeyboardMarkup(inline_keyboard=rows))
    await callback.answer()


@router.callback_query(F.data.startswith("adm:assign:"))
async def assign_manager(callback: CallbackQuery, session: AsyncSession) -> None:
    _, _, order_id, manager_id = callback.data.split(":")
    order = await session.get(Order, int(order_id))
    manager = await session.get(Manager, int(manager_id))
    if order is None or manager is None or not manager.is_active:
        await callback.answer("Заказ или менеджер недоступен", show_alert=True)
        return
    order.manager_id = manager.id
    await callback.answer("Менеджер назначен")
    await orders(callback, session)
