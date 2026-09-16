from aiogram import Bot, Dispatcher

from bots.common import register_error_handler
from config import Settings
from database.database import Database
from handlers.admin import router
from middleware import AdminMiddleware, DatabaseMiddleware


async def run_admin_bot(settings: Settings, database: Database) -> None:
    bot = Bot(settings.admin_bot_token)
    user_notification_bot = Bot(settings.user_bot_token)
    dispatcher = Dispatcher(settings=settings, user_notification_bot=user_notification_bot)
    dispatcher.update.outer_middleware(AdminMiddleware(settings))
    dispatcher.update.outer_middleware(DatabaseMiddleware(database))
    dispatcher.include_router(router())
    register_error_handler(dispatcher)
    try:
        await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())
    finally:
        await user_notification_bot.session.close()
