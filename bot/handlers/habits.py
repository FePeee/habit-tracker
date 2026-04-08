from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from api_client import api

router = Router()


class AddHabit(StatesGroup):
    waiting_name = State()
    waiting_time = State()


async def _require_registration(message: Message) -> str | None:
    """Returns telegram_id if registered, otherwise sends a message and returns None."""
    telegram_id = str(message.from_user.id)
    user = await api.get_user(telegram_id)
    if not user:
        await message.answer("Please register first by sending /start")
        return None
    return telegram_id


@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext):
    telegram_id = await _require_registration(message)
    if not telegram_id:
        return
    await state.set_state(AddHabit.waiting_name)
    await message.answer("What habit do you want to track?\n\nExamples: Running, Read 30 min, Meditation")


@router.message(AddHabit.waiting_name)
async def process_habit_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddHabit.waiting_time)
    await message.answer("Set a daily reminder time (e.g. 08:00)\n\nOr send /skip to add without reminder")


@router.message(AddHabit.waiting_time)
async def process_habit_time(message: Message, state: FSMContext):
    data = await state.get_data()
    telegram_id = str(message.from_user.id)
    text = message.text.strip()

    if text.lower() == "/skip":
        reminder_time = None
    else:
        try:
            hour, minute = map(int, text.split(":"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
            reminder_time = f"{hour:02d}:{minute:02d}"
        except (ValueError, AttributeError):
            await message.answer("Invalid time format. Please use HH:MM (e.g. 08:00) or /skip")
            return

    r = await api.create_habit(telegram_id, data["name"], reminder_time)
    await state.clear()

    if r.status_code == 200:
        reminder_text = f" -- reminder at {reminder_time}" if reminder_time else ""
        await message.answer(f"Habit added: {data['name']}{reminder_text}")
    else:
        await message.answer("Error adding habit. Please try again.")


@router.message(Command("list"))
async def cmd_list(message: Message):
    telegram_id = str(message.from_user.id)
    habits = await api.get_habits(telegram_id)
    if habits is None:
        await message.answer("Please register first by sending /start")
        return
    if not habits:
        await message.answer("You have no habits yet. Add one with /add")
        return
    text = "Your habits:\n\n"
    for h in habits:
        status = "done" if h["done_today"] else "todo"
        text += f"{'[x]' if h['done_today'] else '[ ]'} {h['name']}\n"
    await message.answer(text)


@router.message(Command("done"))
async def cmd_done(message: Message):
    telegram_id = str(message.from_user.id)
    habits = await api.get_habits(telegram_id)
    if habits is None:
        await message.answer("Please register first by sending /start")
        return
    if not habits:
        await message.answer("No habits found. Add one with /add")
        return
    pending = [h for h in habits if not h["done_today"]]
    if not pending:
        await message.answer("All habits completed for today! Great job!")
        return
    buttons = [
        [InlineKeyboardButton(text=f"Done: {h['name']}", callback_data=f"complete:{h['id']}")]
        for h in pending
    ]
    await message.answer("Which habit did you complete today?", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("complete:"))
async def callback_complete(callback: CallbackQuery):
    habit_id = callback.data.split(":")[1]
    telegram_id = str(callback.from_user.id)
    r = await api.complete_habit(telegram_id, habit_id)
    if r.status_code == 200:
        streak = r.json().get("streak", 0)
        await callback.answer(f"Done! Streak: {streak} days")
        await callback.message.edit_text(f"Marked as complete! Current streak: {streak} days")
    else:
        await callback.answer("Error. Try again.")


@router.message(Command("delete"))
async def cmd_delete(message: Message):
    telegram_id = str(message.from_user.id)
    habits = await api.get_habits(telegram_id)
    if habits is None:
        await message.answer("Please register first by sending /start")
        return
    if not habits:
        await message.answer("No habits to delete.")
        return
    buttons = [
        [InlineKeyboardButton(text=f"Delete: {h['name']}", callback_data=f"delete:{h['id']}")]
        for h in habits
    ]
    await message.answer("Which habit do you want to delete?", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("delete:"))
async def callback_delete(callback: CallbackQuery):
    habit_id = callback.data.split(":")[1]
    telegram_id = str(callback.from_user.id)
    r = await api.delete_habit(telegram_id, habit_id)
    if r.status_code == 200:
        await callback.answer("Deleted!")
        await callback.message.edit_text("Habit deleted.")
    else:
        await callback.answer("Error. Try again.")
