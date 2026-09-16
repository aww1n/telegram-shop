from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def product_actions(product_id: int, in_stock: bool, page: int = 1, favorite: bool = False,
                    photo_count: int = 0, photo_index: int = 0) -> InlineKeyboardMarkup:
    rows = []
    if photo_count > 1:
        rows.append([
            InlineKeyboardButton(text="⬅️", callback_data=f"photo:{product_id}:{(photo_index - 1) % photo_count}:{page}"),
            InlineKeyboardButton(text=f"🖼 {photo_index + 1}/{photo_count}", callback_data="noop"),
            InlineKeyboardButton(text="➡️", callback_data=f"photo:{product_id}:{(photo_index + 1) % photo_count}:{page}"),
        ])
    if in_stock:
        rows.append([InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"cart:add:{product_id}")])
    rows.append([InlineKeyboardButton(text="💔 Убрать из избранного" if favorite else "❤️ В избранное", callback_data=f"fav:toggle:{product_id}")])
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"catalog:{page}"), InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def product_list(products: list[object], page: int, pages: int, prefix: str = "catalog") -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=f"{product.name} · {product.price:g} ₽", callback_data=f"product:{product.id}:{page}")] for product in products]
    rows.append([
        InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}:{max(1, page - 1)}"),
        InlineKeyboardButton(text=f"{page}/{pages}", callback_data="noop"),
        InlineKeyboardButton(text="➡️", callback_data=f"{prefix}:{min(pages, page + 1)}"),
    ])
    rows.append([InlineKeyboardButton(text="🔎 Фильтры", callback_data="filters"), InlineKeyboardButton(text="🔀 Сортировка", callback_data="sort")])
    rows.append([InlineKeyboardButton(text="◀️ Меню", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
