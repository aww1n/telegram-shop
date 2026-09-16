from decimal import Decimal
from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Category, Product, ProductPhoto
from handlers.admin.common import edit
from keyboards.admin import admin_back
from states.admin import ProductBulk, ProductCreate, ProductEdit
from utils.formatting import money
from utils.validators import non_negative_int, positive_decimal

router = Router(name="admin_products")


async def product_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    products = list((await session.scalars(select(Product).order_by(Product.created_at.desc()).limit(30))).all())
    rows = [[InlineKeyboardButton(text=("✅ " if p.is_active else "🚫 ") + p.name, callback_data=f"adm:product:{p.id}")] for p in products]
    rows.extend([[InlineKeyboardButton(text="➕ Добавить товар", callback_data="adm:product:add")],
                 [InlineKeyboardButton(text="🧰 Массовые операции", callback_data="adm:bulk:start")],
                 [InlineKeyboardButton(text="◀️ Админ-панель", callback_data="adm:home")]])
    await edit(callback, "📦 <b>Товары</b>", InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data == "adm:products")
async def products(callback: CallbackQuery, session: AsyncSession) -> None:
    await product_menu(callback, session)
    await callback.answer()


@router.callback_query(F.data.regexp(r"^adm:product:\d+$"))
async def detail(callback: CallbackQuery, session: AsyncSession) -> None:
    product = await session.get(Product, int(callback.data.rsplit(":", 1)[1]))
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Изменить цену", callback_data=f"adm:product:price:{product.id}"),
         InlineKeyboardButton(text="📦 Изменить остаток", callback_data=f"adm:product:stock:{product.id}")],
        [InlineKeyboardButton(text="✏️ Остальные поля", callback_data=f"adm:product:fields:{product.id}"),
         InlineKeyboardButton(text="🖼 Фото", callback_data=f"adm:product:photos:{product.id}")],
        [InlineKeyboardButton(text="Скрыть" if product.is_active else "Показать", callback_data=f"adm:product:toggle:{product.id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"adm:product:delete:ask:{product.id}")],
        [InlineKeyboardButton(text="◀️ Товары", callback_data="adm:products")],
    ])
    await edit(callback, f"📦 <b>{escape(product.name)}</b>\nАртикул: {escape(product.article)}\nЦена: {money(product.price)}\nОстаток: {product.stock}\nСтатус: {'показан' if product.is_active else 'скрыт'}", keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("adm:product:fields:"))
async def edit_fields(callback: CallbackQuery) -> None:
    product_id = int(callback.data.rsplit(":", 1)[1])
    fields = (("Название", "name"), ("Краткое описание", "short_description"), ("Описание", "description"),
              ("Характеристики", "characteristics"), ("Артикул", "article"), ("Категория", "category_id"))
    rows = [[InlineKeyboardButton(text=label, callback_data=f"adm:field:{name}:{product_id}")] for label, name in fields]
    rows.append([InlineKeyboardButton(text="◀️ К товару", callback_data=f"adm:product:{product_id}")])
    await edit(callback, "Что изменить?", InlineKeyboardMarkup(inline_keyboard=rows))
    await callback.answer()


@router.callback_query(F.data.startswith("adm:field:"))
async def edit_field_start(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, field, product_id = callback.data.split(":")
    await state.set_state(ProductEdit.value)
    await state.update_data(product_id=int(product_id), field=field)
    prompt = "Введите ID категории:" if field == "category_id" else "Введите новое значение:"
    await edit(callback, prompt + " /cancel — отмена.")
    await callback.answer()


@router.message(ProductEdit.value)
async def edit_field_finish(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    product = await session.get(Product, data["product_id"])
    if product is None:
        await state.clear()
        await message.answer("Товар не найден.")
        return
    field, value = data["field"], (message.text or "").strip()
    if field == "category_id":
        try:
            category_id = int(value)
        except ValueError:
            await message.answer("Введите числовой ID категории.")
            return
        if await session.get(Category, category_id) is None:
            await message.answer("Категория не найдена.")
            return
        setattr(product, field, category_id)
    else:
        limits = {"name": 256, "short_description": 500, "article": 64}
        if not value or len(value) > limits.get(field, 10_000):
            await message.answer("Значение пустое или слишком длинное.")
            return
        if field == "article" and await session.scalar(select(Product.id).where(Product.article == value, Product.id != product.id)):
            await message.answer("Такой артикул уже существует.")
            return
        setattr(product, field, value)
    await state.clear()
    await message.answer("Товар обновлён.", reply_markup=admin_back())


@router.callback_query(F.data.startswith("adm:product:photos:"))
async def photo_menu(callback: CallbackQuery) -> None:
    product_id = int(callback.data.rsplit(":", 1)[1])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить фото", callback_data=f"adm:photo:add:{product_id}")],
        [InlineKeyboardButton(text="🗑 Удалить все фото", callback_data=f"adm:photo:clear:ask:{product_id}")],
        [InlineKeyboardButton(text="◀️ К товару", callback_data=f"adm:product:{product_id}")],
    ])
    await edit(callback, "Управление фотографиями:", keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("adm:photo:add:"))
async def photo_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ProductEdit.photo)
    await state.update_data(product_id=int(callback.data.rsplit(":", 1)[1]))
    await edit(callback, "Отправьте новую фотографию. /cancel — отмена.")
    await callback.answer()


@router.message(ProductEdit.photo, F.photo)
async def photo_add_finish(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    product = await session.get(Product, data["product_id"])
    if product is None:
        await state.clear()
        await message.answer("Товар не найден.")
        return
    count = len(list((await session.scalars(select(ProductPhoto.id).where(ProductPhoto.product_id == product.id))).all()))
    session.add(ProductPhoto(product_id=product.id, telegram_file_id=message.photo[-1].file_id, sort_order=count))
    await state.clear()
    await message.answer("Фотография добавлена.", reply_markup=admin_back())


@router.callback_query(F.data.startswith("adm:photo:clear:ask:"))
async def photo_clear_ask(callback: CallbackQuery) -> None:
    product_id = int(callback.data.rsplit(":", 1)[1])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Удалить все", callback_data=f"adm:photo:clear:yes:{product_id}")],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data=f"adm:product:photos:{product_id}")],
    ])
    await edit(callback, "Удалить все фотографии товара?", keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("adm:photo:clear:yes:"))
async def photo_clear(callback: CallbackQuery, session: AsyncSession) -> None:
    product_id = int(callback.data.rsplit(":", 1)[1])
    photos = list((await session.scalars(select(ProductPhoto).where(ProductPhoto.product_id == product_id))).all())
    for photo in photos:
        await session.delete(photo)
    await edit(callback, "Фотографии удалены.", admin_back())
    await callback.answer()


@router.callback_query(F.data.startswith("adm:product:price:"))
async def edit_price_start(callback: CallbackQuery, state: FSMContext) -> None:
    product_id = int(callback.data.rsplit(":", 1)[1])
    await state.set_state(ProductEdit.price)
    await state.update_data(product_id=product_id)
    await edit(callback, "Введите новую цену. /cancel — отмена.")
    await callback.answer()


@router.message(ProductEdit.price)
async def edit_price_finish(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        value = positive_decimal(message.text or "")
    except ValueError as error:
        await message.answer(str(error))
        return
    data = await state.get_data()
    product = await session.get(Product, data["product_id"])
    if product is None:
        await state.clear()
        await message.answer("Товар не найден.")
        return
    product.price = value
    await state.clear()
    await message.answer("Цена обновлена.", reply_markup=admin_back())


@router.callback_query(F.data.startswith("adm:product:stock:"))
async def edit_stock_start(callback: CallbackQuery, state: FSMContext) -> None:
    product_id = int(callback.data.rsplit(":", 1)[1])
    await state.set_state(ProductEdit.stock)
    await state.update_data(product_id=product_id)
    await edit(callback, "Введите новый остаток. /cancel — отмена.")
    await callback.answer()


@router.message(ProductEdit.stock)
async def edit_stock_finish(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        value = non_negative_int(message.text or "")
    except ValueError as error:
        await message.answer(str(error))
        return
    data = await state.get_data()
    product = await session.get(Product, data["product_id"])
    if product is None:
        await state.clear()
        await message.answer("Товар не найден.")
        return
    product.stock = value
    await state.clear()
    await message.answer("Остаток обновлён.", reply_markup=admin_back())


@router.callback_query(F.data == "adm:bulk:start")
async def bulk_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ProductBulk.ids)
    await edit(callback, "Введите ID товаров через запятую, например: 1,2,5. /cancel — отмена.")
    await callback.answer()


@router.message(ProductBulk.ids)
async def bulk_ids(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        ids = sorted({int(part.strip()) for part in (message.text or "").split(",") if part.strip()})
    except ValueError:
        await message.answer("ID должны быть целыми числами через запятую.")
        return
    existing = set((await session.scalars(select(Product.id).where(Product.id.in_(ids)))).all()) if ids else set()
    if not existing:
        await message.answer("Товары не найдены.")
        return
    await state.update_data(ids=sorted(existing))
    await state.set_state(ProductBulk.action)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🙈 Скрыть", callback_data="adm:bulk:hide"), InlineKeyboardButton(text="👁 Показать", callback_data="adm:bulk:show")],
        [InlineKeyboardButton(text="💰 Цена", callback_data="adm:bulk:price"), InlineKeyboardButton(text="📦 Остаток", callback_data="adm:bulk:stock")],
        [InlineKeyboardButton(text="📂 Категория", callback_data="adm:bulk:category")],
    ])
    await message.answer(f"Выбрано товаров: {len(existing)}. Что изменить?", reply_markup=keyboard)


@router.callback_query(ProductBulk.action, F.data.startswith("adm:bulk:"))
async def bulk_action(callback: CallbackQuery, state: FSMContext) -> None:
    action = callback.data.rsplit(":", 1)[1]
    await state.update_data(action=action)
    if action in {"hide", "show"}:
        await state.update_data(value=action == "show")
        await bulk_confirm_prompt(callback, state)
        return
    await state.set_state(ProductBulk.value)
    prompts = {"price": "Введите новую цену:", "stock": "Введите новый остаток:", "category": "Введите ID новой категории:"}
    await edit(callback, prompts[action])
    await callback.answer()


@router.message(ProductBulk.value)
async def bulk_value(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    action = data["action"]
    try:
        if action == "price":
            value: object = str(positive_decimal(message.text or ""))
        elif action == "stock":
            value = non_negative_int(message.text or "")
        else:
            value = int(message.text or "")
            if await session.get(Category, value) is None:
                raise ValueError("Категория не найдена")
    except ValueError as error:
        await message.answer(str(error))
        return
    await state.update_data(value=value)
    await state.set_state(ProductBulk.confirm)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="adm:bulk:confirm")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="adm:product:cancel")],
    ])
    await message.answer(f"Изменить {len(data['ids'])} товаров? Новое значение: {value}", reply_markup=keyboard)


async def bulk_confirm_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(ProductBulk.confirm)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="adm:bulk:confirm")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="adm:product:cancel")],
    ])
    await edit(callback, f"Применить операцию «{data['action']}» к {len(data['ids'])} товарам?", keyboard)
    await callback.answer()


@router.callback_query(ProductBulk.confirm, F.data == "adm:bulk:confirm")
async def bulk_apply(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    action, value = data["action"], data["value"]
    field = {"hide": Product.is_active, "show": Product.is_active, "price": Product.price,
             "stock": Product.stock, "category": Product.category_id}[action]
    if action == "price":
        value = Decimal(value)
    result = await session.execute(update(Product).where(Product.id.in_(data["ids"])).values({field.key: value}))
    await state.clear()
    await edit(callback, f"Готово. Изменено товаров: {result.rowcount}.", admin_back())
    await callback.answer()


@router.callback_query(F.data.startswith("adm:product:toggle:"))
async def toggle(callback: CallbackQuery, session: AsyncSession) -> None:
    product = await session.get(Product, int(callback.data.rsplit(":", 1)[1]))
    if product:
        product.is_active = not product.is_active
        await callback.answer("Статус изменён")
        await product_menu(callback, session)


@router.callback_query(F.data.startswith("adm:product:delete:ask:"))
async def delete_ask(callback: CallbackQuery) -> None:
    product_id = int(callback.data.rsplit(":", 1)[1])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Удалить", callback_data=f"adm:product:delete:yes:{product_id}")],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data=f"adm:product:{product_id}")],
    ])
    await edit(callback, "Удалить товар? Для сохранения истории заказов позиции заказа останутся.", keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("adm:product:delete:yes:"))
async def delete_product(callback: CallbackQuery, session: AsyncSession) -> None:
    product = await session.get(Product, int(callback.data.rsplit(":", 1)[1]))
    if product:
        await session.delete(product)
    await product_menu(callback, session)
    await callback.answer("Товар удалён")


@router.callback_query(F.data == "adm:product:add")
async def create_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ProductCreate.photos)
    await state.update_data(photos=[])
    await edit(callback, "Отправьте фото товара. Можно несколько по одному. Когда закончите, отправьте /skip. Для товара без фото сразу /skip.")
    await callback.answer()


@router.message(ProductCreate.photos, F.photo)
async def create_photo(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    photos = list(data.get("photos", []))
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"Фото добавлено ({len(photos)}). Ещё фото или /skip.")


@router.message(ProductCreate.photos, F.text == "/skip")
async def create_name_prompt(message: Message, state: FSMContext) -> None:
    await state.set_state(ProductCreate.name)
    await message.answer("Введите название:")


@router.message(ProductCreate.name)
async def create_name(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if not 1 <= len(value) <= 256:
        await message.answer("Название должно содержать от 1 до 256 символов.")
        return
    await state.update_data(name=value)
    await state.set_state(ProductCreate.short_description)
    await message.answer("Введите краткое описание:")


@router.message(ProductCreate.short_description)
async def create_short(message: Message, state: FSMContext) -> None:
    await state.update_data(short_description=(message.text or "").strip()[:500])
    await state.set_state(ProductCreate.description)
    await message.answer("Введите полное описание:")


@router.message(ProductCreate.description)
async def create_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=(message.text or "").strip())
    await state.set_state(ProductCreate.price)
    await message.answer("Введите цену:")


@router.message(ProductCreate.price)
async def create_price(message: Message, state: FSMContext) -> None:
    try:
        value = positive_decimal(message.text or "")
    except ValueError as error:
        await message.answer(str(error))
        return
    await state.update_data(price=str(value))
    await state.set_state(ProductCreate.category)
    await message.answer("Введите ID категории (посмотреть ID можно в разделе категорий):")


@router.message(ProductCreate.category)
async def create_category(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        category_id = int(message.text or "")
    except ValueError:
        await message.answer("Введите числовой ID категории.")
        return
    if await session.get(Category, category_id) is None:
        await message.answer("Категория не найдена.")
        return
    await state.update_data(category_id=category_id)
    await state.set_state(ProductCreate.characteristics)
    await message.answer("Введите характеристики, каждую с новой строки:")


@router.message(ProductCreate.characteristics)
async def create_characteristics(message: Message, state: FSMContext) -> None:
    await state.update_data(characteristics=(message.text or "").strip())
    await state.set_state(ProductCreate.article)
    await message.answer("Введите уникальный артикул:")


@router.message(ProductCreate.article)
async def create_article(message: Message, state: FSMContext, session: AsyncSession) -> None:
    article = (message.text or "").strip()
    if not article or len(article) > 64:
        await message.answer("Артикул обязателен и не должен превышать 64 символа.")
        return
    if await session.scalar(select(Product.id).where(Product.article == article)):
        await message.answer("Такой артикул уже существует.")
        return
    await state.update_data(article=article)
    await state.set_state(ProductCreate.stock)
    await message.answer("Введите остаток:")


@router.message(ProductCreate.stock)
async def create_stock(message: Message, state: FSMContext) -> None:
    try:
        stock = non_negative_int(message.text or "")
    except ValueError as error:
        await message.answer(str(error))
        return
    await state.update_data(stock=stock)
    data = await state.get_data()
    await state.set_state(ProductCreate.preview)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Сохранить", callback_data="adm:product:save")], [InlineKeyboardButton(text="❌ Отмена", callback_data="adm:product:cancel")]])
    await message.answer(f"📦 <b>{escape(data['name'])}</b>\n\n{escape(data['description'])}\n\n📋 {escape(data['characteristics'])}\n🏷 {escape(data['article'])}\n💰 {money(data['price'])}\n📦 Остаток: {stock}", reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(ProductCreate.preview, F.data == "adm:product:save")
async def create_save(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    product = Product(name=data["name"], short_description=data["short_description"], description=data["description"],
                      price=Decimal(data["price"]), category_id=data["category_id"], characteristics=data["characteristics"],
                      article=data["article"], stock=data["stock"])
    product.photos = [ProductPhoto(telegram_file_id=file_id, sort_order=index) for index, file_id in enumerate(data["photos"])]
    session.add(product)
    await state.clear()
    await edit(callback, "✅ Товар сохранён.", admin_back())
    await callback.answer()


@router.callback_query(F.data == "adm:product:cancel")
async def create_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await edit(callback, "Создание отменено.", admin_back())
    await callback.answer()
