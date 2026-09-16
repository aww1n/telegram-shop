import logging

from aiogram import Dispatcher
from aiogram.types import ErrorEvent

logger = logging.getLogger(__name__)


def register_error_handler(dispatcher: Dispatcher) -> None:
    @dispatcher.errors()
    async def errors(event: ErrorEvent) -> bool:
        logger.exception("Unhandled Telegram update error", exc_info=event.exception)
        update = event.update
        message = update.message or (update.callback_query.message if update.callback_query else None)
        if message:
            try:
                await message.answer("⚠️ Произошла ошибка.\n\nПопробуйте ещё раз.")
            except Exception:
                logger.exception("Unable to deliver safe error message")
        return True
