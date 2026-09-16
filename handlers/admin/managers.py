from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Manager, Order, OrderStatus
from handlers.admin.common import edit

router = Router(name="admin_managers")


@router.callback_query(F.data == "adm:managers")
async def managers(callback: CallbackQuery, session: AsyncSession) -> None:
    entries = list((await session.scalars(select(Manager).order_by(Manager.id))).all())
    lines = ["👨‍💼 <b>Менеджеры</b>", ""]
    for manager in entries:
        total = int(await session.scalar(select(func.count(Order.id)).where(Order.manager_id == manager.id)) or 0)
        active = int(await session.scalar(select(func.count(Order.id)).where(Order.manager_id == manager.id, Order.status.in_((OrderStatus.NEW, OrderStatus.PROCESSING, OrderStatus.ACCEPTED)))) or 0)
        lines.append(f"@{manager.username}: всего {total}, активных {active}")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Админ-панель", callback_data="adm:home")]])
    await edit(callback, "\n".join(lines), keyboard)
    await callback.answer()
