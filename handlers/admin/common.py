from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery


async def edit(callback: CallbackQuery, text: str, reply_markup: object | None = None) -> None:
    if not callback.message:
        return
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
