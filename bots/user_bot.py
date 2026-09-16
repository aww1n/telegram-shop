from aiogram import Bot, Dispatcher

from bots.common import register_error_handler
from config import Settings
from database.database import Database
from handlers.user import router
from middleware import DatabaseMiddleware


async def run_user_bot(settings: Settings, database: Database) -> None:
    bot = Bot(settings.user_bot_token)
    admin_notification_bot = Bot(settings.admin_bot_token)
    dispatcher = Dispatcher(settings=settings, admin_notification_bot=admin_notification_bot)
    dispatcher.update.outer_middleware(DatabaseMiddleware(database))
    dispatcher.include_router(router())
    register_error_handler(dispatcher)
    try:
        await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())
    finally:
        await admin_notification_bot.session.close()
