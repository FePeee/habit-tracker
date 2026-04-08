from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from api_client import api
from config import TIMEZONES

router = Router()


class Registration(StatesGroup):
    waiting_name = State()
    waiting_timezone = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    args = message.text.split()
    telegram_id = str(message.from_user.id)

    if len(args) > 1:
        r = await api.link_telegram(args[1], telegram_id)
        if r.status_code == 200:
            name = r.json().get("name", "")
            await message.answer(f"Account linked! Welcome, {name}!\n\nUse /help to see all commands.")
        else:
            await message.answer("Invalid code. Try again.")
        return

    user = await api.get_user(telegram_id)
    if user:
        await message.answer(f"Welcome back, {user['name']}!\n\nUse /help to see all commands.")
    else:
        await state.set_state(Registration.waiting_name)
        await message.answer("Welcome to Habit Tracker!\n\nLet's set up your account. What's your name?")


@router.message(Registration.waiting_name)
async def reg_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"tz:{tz}")]
        for label, tz in TIMEZONES
    ]
    await state.set_state(Registration.waiting_timezone)
    await message.answer("Select your timezone:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("tz:"))
async def reg_timezone(callback: CallbackQuery, state: FSMContext):
    tz = callback.data.split(":", 1)[1]
    data = await state.get_data()
    name = data.get("name", callback.from_user.first_name)
    telegram_id = str(callback.from_user.id)

    r = await api.register(telegram_id, name, tz)
    await state.clear()

    if r.status_code == 200:
        await callback.message.edit_text(
            f"Account created!\nName: {name}\nTimezone: {tz}\n\nAdd your first habit with /add"
        )
    else:
        detail = r.json().get("detail", "Error")
        await callback.message.edit_text(f"Error: {detail}")
