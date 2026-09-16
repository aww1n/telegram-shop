import asyncio
import logging
from pathlib import Path

from bots.admin_bot import run_admin_bot
from bots.user_bot import run_user_bot
from config import get_settings
from database.database import Database
from services.manager_service import ManagerService


def configure_logging(level: str) -> None:
    Path("logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler("logs/shop.log", encoding="utf-8"), logging.StreamHandler()],
    )


async def main() -> None:
    settings = get_settings()
    settings.validate_runtime()
    configure_logging(settings.log_level)
    database = Database(settings.database_url)
    await database.create_schema()
    async with database.session_factory() as session:
        await ManagerService(session).sync(settings.manager_usernames)
        await session.commit()
    logging.getLogger(__name__).info("Starting user and admin bots")
    try:
        await asyncio.gather(run_user_bot(settings, database), run_admin_bot(settings, database))
    finally:
        await database.close()
        logging.getLogger(__name__).info("Bots stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped")
