from aiogram import Router

from handlers.user import cart, catalog, favorites, filters, history, orders, search, start


def router() -> Router:
    root = Router(name="user")
    for module in (start, catalog, search, filters, favorites, cart, orders, history):
        root.include_router(module.router)
    return root
