from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Каталог", callback_data="catalog:1"), InlineKeyboardButton(text="📂 Категории", callback_data="categories")],
        [InlineKeyboardButton(text="🔎 Поиск", callback_data="search"), InlineKeyboardButton(text="❤️ Избранное", callback_data="favorites")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart"), InlineKeyboardButton(text="📦 Мои заказы", callback_data="orders")],
        [InlineKeyboardButton(text="🕘 Недавно просмотренные", callback_data="recent")],
        [InlineKeyboardButton(text="ℹ️ Информация", callback_data="info")],
    ])


def back_home() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Главное меню", callback_data="home")]])
