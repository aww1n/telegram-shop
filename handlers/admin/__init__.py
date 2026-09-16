from aiogram import Router

from handlers.admin import categories, dashboard, import_export, managers, orders, products, settings, start, statistics


def router() -> Router:
    root = Router(name="admin")
    for module in (start, dashboard, products, categories, orders, managers, statistics, import_export, settings):
        root.include_router(module.router)
    return root
