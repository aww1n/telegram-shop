from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.admin.common import edit
from services.import_export_service import ImportExportService
from states.admin import CsvImport

router = Router(name="admin_transfer")


@router.callback_query(F.data == "adm:transfer")
async def transfer(callback: CallbackQuery) -> None:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Импорт CSV", callback_data="adm:import")],
        [InlineKeyboardButton(text="📤 Экспорт CSV", callback_data="adm:export")],
        [InlineKeyboardButton(text="◀️ Админ-панель", callback_data="adm:home")],
    ])
    await edit(callback, "📥 <b>Импорт / экспорт</b>", keyboard)
    await callback.answer()


@router.callback_query(F.data == "adm:export")
async def export(callback: CallbackQuery, session: AsyncSession) -> None:
    content = await ImportExportService(session).export_csv()
    if callback.message:
        await callback.message.answer_document(BufferedInputFile(content, filename="products.csv"))
    await callback.answer()


@router.callback_query(F.data == "adm:import")
async def import_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CsvImport.document)
    await edit(callback, "Отправьте CSV-файл UTF-8. Существующие товары с тем же артикулом будут обновлены. /cancel — отмена.")
    await callback.answer()


@router.message(CsvImport.document, F.document)
async def import_file(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    document = message.document
    if document is None or document.file_size and document.file_size > 5_000_000:
        await message.answer("Файл слишком большой (максимум 5 МБ).")
        return
    stream = await bot.download(document)
    result = await ImportExportService(session).import_csv(stream.read())
    await state.clear()
    report = f"Импортировано: {result.imported}."
    if result.errors:
        report += "\n\nОшибки:\n" + "\n".join(result.errors[:30])
    await message.answer(report)
