from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    user_bot_token: str = ""
    admin_bot_token: str = ""
    admin_ids: str = ""
    order_manager_usernames: str = ""
    database_url: str = "sqlite+aiosqlite:///./shop.db"
    low_stock_threshold: int = 3
    recently_viewed_limit: int = 20
    log_level: str = "INFO"

    @property
    def admin_id_values(self) -> tuple[int, ...]:
        try:
            return tuple(int(part.strip()) for part in self.admin_ids.split(",") if part.strip())
        except ValueError as error:
            raise ValueError("ADMIN_IDS must be a comma-separated list of integers") from error

    @property
    def manager_usernames(self) -> tuple[str, ...]:
        return tuple(part.strip().lstrip("@") for part in self.order_manager_usernames.split(",") if part.strip())

    def validate_runtime(self) -> None:
        if not self.user_bot_token or not self.admin_bot_token:
            raise ValueError("USER_BOT_TOKEN and ADMIN_BOT_TOKEN must be set in .env")
        if not self.admin_id_values:
            raise ValueError("ADMIN_IDS must contain at least one Telegram ID")
        if not self.manager_usernames:
            raise ValueError("ORDER_MANAGER_USERNAMES must contain at least one username")


@lru_cache
def get_settings() -> Settings:
    return Settings()
