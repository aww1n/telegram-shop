import logging

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings
from database.repositories.users import UserRepository
from handlers.user.common import edit
from keyboards.user import main_menu

router = Router(name="user_start")
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def start(message: Message, session: AsyncSession, settings: Settings, admin_notification_bot: Bot) -> None:
    user = message.from_user
    if user:
        _, created = await UserRepository(session).upsert(user.id, user.username, user.first_name, user.last_name)
        if created:
            try:
                for admin_id in settings.admin_id_values:
                    await admin_notification_bot.send_message(admin_id, f"👤 Новый пользователь: {user.first_name} (@{user.username or 'без_username'})")
            except Exception:
                logger.exception("Unable to notify administrators about new user")
    await message.answer("👋 <b>Добро пожаловать!</b>\n\nВыберите раздел:", reply_markup=main_menu(), parse_mode="HTML")


@router.callback_query(F.data == "home")
async def home(callback: CallbackQuery) -> None:
    await edit(callback, "👋 <b>Добро пожаловать!</b>\n\nВыберите раздел:", main_menu())
    await callback.answer()


@router.callback_query(F.data == "info")
async def info(callback: CallbackQuery) -> None:
    await edit(callback, "ℹ️ Выберите товар, добавьте его в корзину и нажмите «Оформить заказ». Бот подготовит сообщение менеджеру.", main_menu())
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()
