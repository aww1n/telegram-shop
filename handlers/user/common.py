from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from database.repositories.users import UserRepository


async def current_user(callback: CallbackQuery, session: AsyncSession) -> User:
    source = callback.from_user
    user, _ = await UserRepository(session).upsert(source.id, source.username, source.first_name, source.last_name)
    return user


async def edit(callback: CallbackQuery, text: str, reply_markup: object | None = None) -> None:
    if not callback.message:
        return
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
