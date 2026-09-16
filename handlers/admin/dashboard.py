from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.admin.common import edit
from keyboards.admin import admin_back
from services.analytics_service import AnalyticsService
from utils.formatting import money

router = Router(name="admin_dashboard")


@router.callback_query(F.data == "adm:dashboard")
async def dashboard(callback: CallbackQuery, session: AsyncSession) -> None:
    data = await AnalyticsService(session).for_days(1)
    text = ("📊 <b>DASHBOARD · сегодня</b>\n\n"
            f"👥 Новых пользователей: {data['users']}\n👀 Просмотров: {data['view']}\n"
            f"❤️ Добавлений в избранное: {data['favorite_add']}\n🛒 Добавлений в корзину: {data['cart_add']}\n"
            f"📨 Заказов: {data['orders']}\n💰 Сумма заказов: {money(data['revenue'])}\n\n"
            f"📦 Товаров: {data['products']}\n❌ Нет в наличии: {data['out_of_stock']}")
    await edit(callback, text, admin_back())
    await callback.answer()
