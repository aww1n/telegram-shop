# Telegram Shop

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![aiogram 3](https://img.shields.io/badge/aiogram-3.x-26A5E4?logo=telegram&logoColor=white)](https://docs.aiogram.dev/)
[![Tests](https://github.com/aww1n/telegram-shop/actions/workflows/tests.yml/badge.svg)](https://github.com/aww1n/telegram-shop/actions/workflows/tests.yml)

Асинхронный Telegram-магазин из двух ботов с общей базой данных. User Bot отвечает за каталог, поиск, избранное, корзину и заказы. Admin Bot управляет каталогом, категориями, заказами, менеджерами, CSV и аналитикой. Заказ передаётся менеджеру через Telegram deep link: бот подготавливает текст, а пользователь сам нажимает «Отправить».

## Требования

- Python 3.12 или новее
- два Telegram bot token от BotFather
- Telegram ID администраторов
- username хотя бы одного менеджера

Docker не требуется и в проекте не используется.

## Установка

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Заполните `.env`:

```dotenv
USER_BOT_TOKEN=123:token
ADMIN_BOT_TOKEN=456:token
ADMIN_IDS=123456789,987654321
ORDER_MANAGER_USERNAMES=manager1,manager2
DATABASE_URL=sqlite+aiosqlite:///./shop.db
LOW_STOCK_THRESHOLD=3
RECENTLY_VIEWED_LIMIT=20
LOG_LEVEL=INFO
```

Username менеджера указывается без `@`. Первый активный менеджер используется как основной. Токены и рабочая база исключены из Git.

## Миграции и запуск

```bash
alembic upgrade head
python main.py
```

`main.py` запускает оба long polling процесса одновременно и корректно закрывает соединения при остановке. При первом запуске схема также безопасно создаётся из metadata, однако в рабочих окружениях следует применять миграции перед запуском.

После запуска откройте оба бота и отправьте `/start`. Admin Bot проверяет Telegram ID на уровне middleware до обработки любого сообщения или callback. `/cancel` завершает активный административный FSM-сценарий.

## Основные возможности

- каталог, категории и подкатегории, пагинация, сортировка, регистронезависимый частичный поиск;
- карточки с Telegram `file_id`, характеристиками, остатком и ценой;
- избранное и последние 20 просмотренных товаров без дублей;
- корзина с проверкой остатка при каждом изменении;
- атомарное создание заказа, снимки названия, артикула и цены в `order_items`;
- история заказов и контролируемые переходы статусов;
- deep link с URL-кодированием кириллицы, emoji, переносов и знака рубля;
- административный dashboard, категории, товары через FSM, скрытие и безопасное удаление;
- управление статусами заказов, менеджеры, аналитика по периодам;
- импорт и экспорт UTF-8 CSV с отчётом по ошибочным строкам;
- глобальный безопасный обработчик ошибок и файловое логирование без секретов.

## CSV

Экспорт создаёт шаблон с колонками:

```text
name,short_description,description,price,category,characteristics,article,stock
```

При импорте товар с существующим артикулом обновляется. Отсутствующая категория создаётся. Файл должен быть UTF-8 и не больше 5 МБ; ошибки содержат номер строки и причину.

## Резервная копия

SQLite Online Backup API создаёт согласованную копию без остановки приложения:

```bash
python scripts/backup_sqlite.py
python scripts/backup_sqlite.py /safe/path/shop-backup.db
```

По умолчанию копия появляется в `backup/`. Регулярно переносите её на другой носитель и периодически проверяйте восстановление командой `sqlite3 backup.db 'PRAGMA integrity_check;'`.

## Тестирование

```bash
pytest -q
python -m compileall -q .
```

Тесты используют отдельную временную SQLite-базу и проверяют корзину, сумму, остатки, избранное, создание заказа, снимки данных, статусы, deep link, URL encoding и права администратора. Полный Telegram-сценарий требует тестовых bot token: создайте категорию и товар в Admin Bot, затем пройдите каталог → товар → избранное → корзина → заказ в User Bot.

## Структура

```text
bots/                    запуск и общая обработка ошибок
handlers/user/           пользовательские Telegram-сценарии
handlers/admin/          административные Telegram-сценарии и FSM
keyboards/               inline-клавиатуры
states/                  FSM-состояния
database/models.py       SQLAlchemy-модели и индексы
database/repositories/   запросы каталога, пользователей и аналитики
services/                бизнес-логика корзины, заказов, импорта и уведомлений
utils/                   форматирование, deep links, валидация, пагинация
alembic/                 миграции схемы
scripts/backup_sqlite.py online backup SQLite
tests/                   изолированные тесты доменной логики
main.py                  одновременный запуск двух ботов
```

Архитектура не использует SQLite-специфичные запросы в бизнес-логике. Для перехода на PostgreSQL замените `DATABASE_URL`, установите async-драйвер и примените Alembic-миграции.
