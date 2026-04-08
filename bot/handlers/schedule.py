from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from api_client import api
from config import TIMEZONES

router = Router()

DAYS = [
    ("Monday", "monday"),
    ("Tuesday", "tuesday"),
    ("Wednesday", "wednesday"),
    ("Thursday", "thursday"),
    ("Friday", "friday"),
    ("Saturday", "saturday"),
    ("Sunday", "sunday"),
]

DAY_NAMES = dict((v, k) for k, v in DAYS)


class ScheduleReport(StatesGroup):
    waiting_day = State()
    waiting_time = State()


@router.message(Command("schedule"))
async def cmd_schedule(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    user = await api.get_user(telegram_id)
    if not user:
        await message.answer("Please register first by sending /start")
        return

    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"rday:{day}")]
        for label, day in DAYS
    ]
    await message.answer(
        "Weekly Report Schedule\n\n"
        "Choose a day of the week to receive your automatic AI report:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await state.set_state(ScheduleReport.waiting_day)


@router.callback_query(F.data.startswith("rday:"))
async def callback_report_day(callback: CallbackQuery, state: FSMContext):
    day = callback.data.split(":", 1)[1]
    await state.update_data(report_day=day)
    await state.set_state(ScheduleReport.waiting_time)
    await callback.message.edit_text(
        "Great! Now tell me what time you'd like to receive the report (e.g., 18:00 or 09:00):"
    )


@router.message(ScheduleReport.waiting_time)
async def process_report_time(message: Message, state: FSMContext):
    time_text = message.text.strip()
    try:
        hour, minute = map(int, time_text.split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except (ValueError, IndexError):
        await message.answer("Invalid time format. Please use HH:MM (e.g., 18:00)")
        return

    data = await state.get_data()
    report_day = data.get("report_day")
    telegram_id = str(message.from_user.id)

    r = await api.update_report_schedule(telegram_id, report_day, time_text)
    await state.clear()

    if r.status_code == 200:
        day_name = DAY_NAMES.get(report_day, report_day)
        await message.answer(
            f"Weekly Report Scheduled!\n\n"
            f"Day: {day_name}\n"
            f"Time: {time_text}\n\n"
            f"Every week at this time, I'll send you an AI-powered habit report."
        )
    else:
        await message.answer("Error saving schedule")


@router.message(Command("timezone"))
async def cmd_timezone(message: Message):
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"settz:{tz}")]
        for label, tz in TIMEZONES
    ]
    await message.answer("Select your timezone:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("settz:"))
async def callback_set_timezone(callback: CallbackQuery):
    tz = callback.data.split(":", 1)[1]
    telegram_id = str(callback.from_user.id)
    r = await api.update_timezone(telegram_id, tz)
    if r.status_code == 200:
        await callback.message.edit_text(f"Timezone updated to {tz}")
    else:
        await callback.answer("Error. Try again.")
