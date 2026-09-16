from urllib.parse import quote

from database.models import Order
from utils.formatting import money


def order_message(order: Order) -> str:
    lines = ["Здравствуйте! Хочу оформить заказ:", "", "🛒 Состав заказа:", ""]
    for item in order.items:
        lines.extend((f"• {item.product_name} × {item.quantity}", f"  Артикул: {item.article}", ""))
    lines.append(f"💰 Итого: {money(order.total_amount)}")
    lines.append(f"Номер заказа: #{order.id}")
    return "\n".join(lines)


def manager_deep_link(username: str, text: str) -> str:
    clean_username = username.strip().lstrip("@")
    if not clean_username or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_" for character in clean_username):
        raise ValueError("Некорректное имя менеджера")
    return f"https://t.me/{clean_username}?text={quote(text, safe='')}"
