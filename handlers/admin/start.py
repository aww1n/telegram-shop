from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from handlers.admin.common import edit
from keyboards.admin import admin_menu

router = Router(name="admin_start")


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer("⚙️ <b>АДМИН-ПАНЕЛЬ</b>", reply_markup=admin_menu(), parse_mode="HTML")


@router.callback_query(F.data == "adm:home")
async def home(callback: CallbackQuery) -> None:
    await edit(callback, "⚙️ <b>АДМИН-ПАНЕЛЬ</b>", admin_menu())
    await callback.answer()


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=admin_menu())
