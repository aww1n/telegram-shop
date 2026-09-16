from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Category, Product
from handlers.admin.common import edit
from keyboards.admin import admin_back
from states.admin import CategoryCreate, CategoryRename

router = Router(name="admin_categories")


@router.callback_query(F.data == "adm:categories")
async def categories(callback: CallbackQuery, session: AsyncSession) -> None:
    items = list((await session.scalars(select(Category).order_by(Category.name))).all())
    rows = [[InlineKeyboardButton(text=("✅ " if item.is_active else "🚫 ") + f"#{item.id} {item.name}", callback_data=f"adm:cat:view:{item.id}")] for item in items]
    rows.extend([[InlineKeyboardButton(text="➕ Создать", callback_data="adm:cat:add")], [InlineKeyboardButton(text="◀️ Админ-панель", callback_data="adm:home")]])
    await edit(callback, "📂 <b>Категории</b>\nНажмите категорию, чтобы скрыть или показать.", InlineKeyboardMarkup(inline_keyboard=rows))
    await callback.answer()


@router.callback_query(F.data.startswith("adm:cat:view:"))
async def category_detail(callback: CallbackQuery, session: AsyncSession) -> None:
    category = await session.get(Category, int(callback.data.rsplit(":", 1)[1]))
    if category is None:
        await callback.answer("Категория не найдена", show_alert=True)
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Скрыть" if category.is_active else "Показать", callback_data=f"adm:cat:toggle:{category.id}")],
        [InlineKeyboardButton(text="✏️ Переименовать", callback_data=f"adm:cat:rename:{category.id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"adm:cat:delete:ask:{category.id}")],
        [InlineKeyboardButton(text="◀️ Категории", callback_data="adm:categories")],
    ])
    await edit(callback, f"📂 <b>#{category.id} {category.name}</b>", keyboard)
    await callback.answer()


@router.callback_query(F.data == "adm:cat:add")
async def add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CategoryCreate.name)
    await edit(callback, "Введите название категории. Для отмены: /cancel")
    await callback.answer()


@router.message(CategoryCreate.name)
async def add_finish(message: Message, state: FSMContext, session: AsyncSession) -> None:
    name = (message.text or "").strip()
    if not 1 <= len(name) <= 128:
        await message.answer("Название должно содержать от 1 до 128 символов.")
        return
    if await session.scalar(select(Category.id).where(Category.name == name)):
        await message.answer("Такая категория уже существует.")
        return
    session.add(Category(name=name))
    await state.clear()
    await message.answer("Категория создана.", reply_markup=admin_back())


@router.callback_query(F.data.startswith("adm:cat:toggle:"))
async def toggle(callback: CallbackQuery, session: AsyncSession) -> None:
    category = await session.get(Category, int(callback.data.rsplit(":", 1)[1]))
    if category:
        category.is_active = not category.is_active
    await callback.answer("Сохранено")
    await categories(callback, session)


@router.callback_query(F.data.startswith("adm:cat:rename:"))
async def rename_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CategoryRename.name)
    await state.update_data(category_id=int(callback.data.rsplit(":", 1)[1]))
    await edit(callback, "Введите новое название. /cancel — отмена.")
    await callback.answer()


@router.message(CategoryRename.name)
async def rename_finish(message: Message, state: FSMContext, session: AsyncSession) -> None:
    name = (message.text or "").strip()
    data = await state.get_data()
    category = await session.get(Category, data["category_id"])
    if category is None:
        await state.clear()
        await message.answer("Категория не найдена.")
        return
    if not name or len(name) > 128 or await session.scalar(select(Category.id).where(Category.name == name, Category.id != category.id)):
        await message.answer("Название пустое, слишком длинное или уже занято.")
        return
    category.name = name
    await state.clear()
    await message.answer("Категория переименована.", reply_markup=admin_back())


@router.callback_query(F.data.startswith("adm:cat:delete:ask:"))
async def delete_ask(callback: CallbackQuery) -> None:
    category_id = int(callback.data.rsplit(":", 1)[1])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Удалить", callback_data=f"adm:cat:delete:yes:{category_id}")],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data=f"adm:cat:view:{category_id}")],
    ])
    await edit(callback, "Удалить пустую категорию? Категорию с товарами удалить нельзя.", keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("adm:cat:delete:yes:"))
async def delete_category(callback: CallbackQuery, session: AsyncSession) -> None:
    category_id = int(callback.data.rsplit(":", 1)[1])
    if await session.scalar(select(Product.id).where(Product.category_id == category_id).limit(1)):
        await callback.answer("Сначала перенесите товары в другую категорию", show_alert=True)
        return
    category = await session.get(Category, category_id)
    if category:
        await session.delete(category)
    await categories(callback, session)
    await callback.answer("Категория удалена")
