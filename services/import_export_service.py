import csv
import io
from dataclasses import dataclass
from decimal import InvalidOperation

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Category, Product
from utils.validators import non_negative_int, positive_decimal


@dataclass
class ImportResult:
    imported: int
    errors: list[str]


class ImportExportService:
    FIELDS = ("name", "short_description", "description", "price", "category", "characteristics", "article", "stock")

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def export_csv(self) -> bytes:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.FIELDS)
        writer.writeheader()
        products = list((await self.session.scalars(select(Product).order_by(Product.id))).all())
        categories = {item.id: item.name for item in (await self.session.scalars(select(Category))).all()}
        for product in products:
            writer.writerow({"name": product.name, "short_description": product.short_description,
                             "description": product.description, "price": product.price,
                             "category": categories.get(product.category_id, ""), "characteristics": product.characteristics,
                             "article": product.article, "stock": product.stock})
        return output.getvalue().encode("utf-8-sig")

    async def import_csv(self, content: bytes) -> ImportResult:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            return ImportResult(0, ["Файл должен быть в кодировке UTF-8"])
        reader = csv.DictReader(io.StringIO(text))
        missing = set(self.FIELDS) - set(reader.fieldnames or [])
        if missing:
            return ImportResult(0, [f"Нет колонок: {', '.join(sorted(missing))}"])
        imported, errors = 0, []
        for line, row in enumerate(reader, 2):
            try:
                if not row["name"].strip() or not row["article"].strip():
                    raise ValueError("название и артикул обязательны")
                category_name = row["category"].strip()
                category = await self.session.scalar(select(Category).where(Category.name == category_name))
                if category is None:
                    category = Category(name=category_name)
                    self.session.add(category)
                    await self.session.flush()
                product = await self.session.scalar(select(Product).where(Product.article == row["article"].strip()))
                values = {"name": row["name"].strip(), "short_description": row["short_description"].strip(),
                          "description": row["description"].strip(), "price": positive_decimal(row["price"]),
                          "category_id": category.id, "characteristics": row["characteristics"].strip(),
                          "article": row["article"].strip(), "stock": non_negative_int(row["stock"])}
                if product is None:
                    self.session.add(Product(**values))
                else:
                    for key, value in values.items():
                        setattr(product, key, value)
                imported += 1
            except (ValueError, InvalidOperation) as error:
                errors.append(f"Строка {line}: {error}")
        return ImportResult(imported, errors)
