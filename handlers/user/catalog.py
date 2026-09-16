import math

from aiogram import Bot, F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings
from database.models import Favorite
from database.repositories.catalog import CatalogRepository
from handlers.user.common import current_user, edit
from keyboards.product import product_actions, product_list
from keyboards.user import back_home
from services.product_service import ProductService
from utils.formatting import product_text

router = Router(name="user_catalog")
PAGE_SIZE = 6


@router.callback_query(F.data.startswith("catalog:"))
async def catalog(callback: CallbackQuery, session: AsyncSession) -> None:
    page = max(1, int(callback.data.rsplit(":", 1)[1]))
    products, total = await CatalogRepository(session).products(page=page, page_size=PAGE_SIZE)
    pages = max(1, math.ceil(total / PAGE_SIZE))
    if page > pages:
        page = pages
        products, total = await CatalogRepository(session).products(page=page, page_size=PAGE_SIZE)
    text = "🛍 <b>Каталог</b>\n\nВыберите товар:" if products else "Каталог пока пуст."
    markup = product_list(products, page, pages)
    if callback.message and callback.message.photo:
        chat_id = callback.message.chat.id
        await callback.message.delete()
        await callback.bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
    else:
        await edit(callback, text, markup)
    await callback.answer()


@router.callback_query(F.data == "categories")
async def categories(callback: CallbackQuery, session: AsyncSession) -> None:
    categories = await CatalogRepository(session).categories()
    rows = [[InlineKeyboardButton(text=item.name, callback_data=f"category:{item.id}:1")] for item in categories]
    rows.append([InlineKeyboardButton(text="◀️ Меню", callback_data="home")])
    await edit(callback, "📂 <b>Категории</b>", InlineKeyboardMarkup(inline_keyboard=rows))
    await callback.answer()


@router.callback_query(F.data.startswith("category:"))
async def category(callback: CallbackQuery, session: AsyncSession) -> None:
    _, category_id, page = callback.data.split(":")
    products, total = await CatalogRepository(session).products(category_id=int(category_id), page=int(page), page_size=PAGE_SIZE)
    pages = max(1, math.ceil(total / PAGE_SIZE))
    await edit(callback, "📂 <b>Товары категории</b>" if products else "В этой категории пока нет товаров.",
               product_list(products, int(page), pages, prefix=f"category:{category_id}"))
    await callback.answer()


@router.callback_query(F.data.startswith("product:"))
async def product(callback: CallbackQuery, session: AsyncSession, settings: Settings, admin_notification_bot: Bot) -> None:
    _, product_id, page = callback.data.split(":")
    user = await current_user(callback, session)
    item = await CatalogRepository(session).product(int(product_id))
    if item is None:
        await callback.answer("Товар больше недоступен", show_alert=True)
        return
    await ProductService(session, settings.recently_viewed_limit).viewed(user.id, item.id)
    favorite = await session.scalar(select(Favorite.id).where(Favorite.user_id == user.id, Favorite.product_id == item.id))
    markup = product_actions(item.id, item.stock > 0, int(page), bool(favorite), len(item.photos), 0)
    if item.photos and callback.message:
        photo = item.photos[0]
        media: str | BufferedInputFile = photo.user_bot_file_id or await transfer_photo(admin_notification_bot, photo.telegram_file_id, item.id, 0)
        sent = await callback.message.answer_photo(media, caption=product_text(item), reply_markup=markup, parse_mode="HTML")
        if not photo.user_bot_file_id and sent.photo:
            photo.user_bot_file_id = sent.photo[-1].file_id
    else:
        await edit(callback, product_text(item), markup)
    await callback.answer()


@router.callback_query(F.data.startswith("photo:"))
async def photo(callback: CallbackQuery, session: AsyncSession, admin_notification_bot: Bot) -> None:
    _, product_id, index, page = callback.data.split(":")
    item = await CatalogRepository(session).product(int(product_id))
    if item is None or not item.photos or int(index) >= len(item.photos):
        await callback.answer("Фотография недоступна", show_alert=True)
        return
    user = await current_user(callback, session)
    favorite = await session.scalar(select(Favorite.id).where(Favorite.user_id == user.id, Favorite.product_id == item.id))
    markup = product_actions(item.id, item.stock > 0, int(page), bool(favorite), len(item.photos), int(index))
    if callback.message:
        selected = item.photos[int(index)]
        media: str | BufferedInputFile = selected.user_bot_file_id or await transfer_photo(admin_notification_bot, selected.telegram_file_id, item.id, int(index))
        edited = await callback.message.edit_media(InputMediaPhoto(media=media, caption=product_text(item), parse_mode="HTML"), reply_markup=markup)
        if not selected.user_bot_file_id and edited.photo:
            selected.user_bot_file_id = edited.photo[-1].file_id
    await callback.answer()


async def transfer_photo(admin_bot: Bot, admin_file_id: str, product_id: int, index: int) -> BufferedInputFile:
    stream = await admin_bot.download(admin_file_id)
    if stream is None:
        raise ValueError("Не удалось получить фотографию товара")
    return BufferedInputFile(stream.read(), filename=f"product-{product_id}-{index}.jpg")


@router.callback_query(F.data == "sort")
async def sorting(callback: CallbackQuery) -> None:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Популярные", callback_data="sorted:popular:1")],
        [InlineKeyboardButton(text="Сначала дешёвые", callback_data="sorted:cheap:1")],
        [InlineKeyboardButton(text="Сначала дорогие", callback_data="sorted:expensive:1")],
        [InlineKeyboardButton(text="Новые", callback_data="sorted:new:1")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="catalog:1")],
    ])
    await edit(callback, "🔀 <b>Сортировка</b>", keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("sorted:"))
async def sorted_catalog(callback: CallbackQuery, session: AsyncSession) -> None:
    _, sort, page = callback.data.split(":")
    products, total = await CatalogRepository(session).products(sort=sort, page=int(page), page_size=PAGE_SIZE)
    pages = max(1, math.ceil(total / PAGE_SIZE))
    await edit(callback, "🛍 <b>Каталог</b>", product_list(products, int(page), pages, prefix=f"sorted:{sort}"))
    await callback.answer()
