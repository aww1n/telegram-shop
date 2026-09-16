from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def cart_keyboard(items: list[object]) -> InlineKeyboardMarkup:
    rows = []
    for item in items:
        rows.append([
            InlineKeyboardButton(text="➖", callback_data=f"cart:dec:{item.product_id}"),
            InlineKeyboardButton(text=str(item.quantity), callback_data="noop"),
            InlineKeyboardButton(text="➕", callback_data=f"cart:inc:{item.product_id}"),
            InlineKeyboardButton(text="🗑", callback_data=f"cart:remove:{item.product_id}"),
        ])
    if items:
        rows.extend([[InlineKeyboardButton(text="📨 Оформить заказ", callback_data="checkout")],
                     [InlineKeyboardButton(text="🧹 Очистить корзину", callback_data="cart:clear:ask")]])
    rows.append([InlineKeyboardButton(text="◀️ В каталог", callback_data="catalog:1")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
