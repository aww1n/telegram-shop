import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import get_settings


def sqlite_path(url: str) -> Path:
    prefix = "sqlite+aiosqlite:///"
    if not url.startswith(prefix) or url.endswith(":memory:"):
        raise ValueError("Backup script supports only file-based sqlite+aiosqlite databases")
    return Path(url.removeprefix(prefix)).resolve()


def backup(destination: Path | None = None) -> Path:
    source = sqlite_path(get_settings().database_url)
    if not source.is_file():
        raise FileNotFoundError(f"Database not found: {source}")
    target = destination or Path("backup") / f"shop-{datetime.now():%Y%m%d-%H%M%S}.db"
    target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(source) as source_connection, sqlite3.connect(target) as target_connection:
        source_connection.backup(target_connection)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a consistent online SQLite backup")
    parser.add_argument("destination", nargs="?", type=Path)
    arguments = parser.parse_args()
    print(backup(arguments.destination))
