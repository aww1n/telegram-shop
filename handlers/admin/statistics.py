from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.admin.common import edit
from services.analytics_service import AnalyticsService
from utils.formatting import money

router = Router(name="admin_statistics")


@router.callback_query(F.data == "adm:analytics")
async def analytics_menu(callback: CallbackQuery) -> None:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сегодня", callback_data="adm:stats:1"), InlineKeyboardButton(text="7 дней", callback_data="adm:stats:7")],
        [InlineKeyboardButton(text="30 дней", callback_data="adm:stats:30"), InlineKeyboardButton(text="90 дней", callback_data="adm:stats:90")],
        [InlineKeyboardButton(text="Всё время", callback_data="adm:stats:all")],
        [InlineKeyboardButton(text="◀️ Админ-панель", callback_data="adm:home")],
    ])
    await edit(callback, "📈 Выберите период:", keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("adm:stats:"))
async def stats(callback: CallbackQuery, session: AsyncSession) -> None:
    value = callback.data.rsplit(":", 1)[1]
    data = await AnalyticsService(session).for_days(None if value == "all" else int(value))
    text = (f"📈 <b>Аналитика · {value if value == 'all' else value + ' дн.'}</b>\n\n"
            f"Пользователи: {data['users']}\nПросмотры: {data['view']}\n"
            f"Избранное: +{data['favorite_add']} / −{data['favorite_remove']}\n"
            f"Корзина: +{data['cart_add']} / −{data['cart_remove']}\n"
            f"Заказы: {data['orders']}\nСумма: {money(data['revenue'])}")
    await edit(callback, text, InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Периоды", callback_data="adm:analytics")]]))
    await callback.answer()
