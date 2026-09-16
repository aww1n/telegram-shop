from aiogram import F, Router
from aiogram.types import CallbackQuery

from config import Settings
from handlers.admin.common import edit
from keyboards.admin import admin_back

router = Router(name="admin_settings")


@router.callback_query(F.data == "adm:settings")
async def settings_view(callback: CallbackQuery, settings: Settings) -> None:
    await edit(callback, f"⚙️ <b>Настройки</b>\n\nМенеджеров: {len(settings.manager_usernames)}\nПорог малого остатка: {settings.low_stock_threshold}\nЛимит недавних товаров: {settings.recently_viewed_limit}\n\nСекреты и системные настройки изменяются в .env с последующим перезапуском.", admin_back())
    await callback.answer()


@router.callback_query(F.data == "adm:notifications")
async def notifications_view(callback: CallbackQuery) -> None:
    await edit(callback, "🔔 <b>Уведомления</b>\n\nВключены: новые пользователи, новые заказы, низкий остаток и изменение статуса заказа. Пользовательские предпочтения сохраняются в базе.", admin_back())
    await callback.answer()
