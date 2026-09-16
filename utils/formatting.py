from decimal import Decimal
from html import escape

from database.models import OrderStatus, Product


STATUS_NAMES = {
    OrderStatus.NEW: "🆕 Новый", OrderStatus.PROCESSING: "🟡 В обработке",
    OrderStatus.ACCEPTED: "🟢 Принят", OrderStatus.COMPLETED: "🔵 Завершён",
    OrderStatus.CANCELLED: "🔴 Отменён", OrderStatus.REJECTED: "❌ Отклонён",
}


def money(value: Decimal | int | str) -> str:
    number = Decimal(value)
    return f"{number:,.2f}".replace(",", " ").replace(".00", "") + " ₽"


def product_text(product: Product) -> str:
    characteristics = "\n".join(f"• {escape(line.strip())}" for line in product.characteristics.splitlines() if line.strip()) or "• Не указаны"
    availability = f"📦 В наличии: {product.stock} шт." if product.stock > 0 else "❌ Нет в наличии"
    return (f"📦 <b>{escape(product.name)}</b>\n\n{escape(product.short_description)}\n\n"
            f"{escape(product.description)}\n\n📋 <b>Характеристики:</b>\n{characteristics}\n\n"
            f"🏷 Артикул: <code>{escape(product.article)}</code>\n💰 Цена: {money(product.price)}\n{availability}")
