from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Dashboard", callback_data="adm:dashboard"), InlineKeyboardButton(text="📦 Товары", callback_data="adm:products")],
        [InlineKeyboardButton(text="📂 Категории", callback_data="adm:categories"), InlineKeyboardButton(text="📋 Заказы", callback_data="adm:orders")],
        [InlineKeyboardButton(text="👨‍💼 Менеджеры", callback_data="adm:managers"), InlineKeyboardButton(text="📈 Аналитика", callback_data="adm:analytics")],
        [InlineKeyboardButton(text="📥 Импорт / 📤 Экспорт", callback_data="adm:transfer")],
        [InlineKeyboardButton(text="🔔 Уведомления", callback_data="adm:notifications"), InlineKeyboardButton(text="⚙️ Настройки", callback_data="adm:settings")],
    ])


def admin_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Админ-панель", callback_data="adm:home")]])
