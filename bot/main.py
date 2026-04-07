import asyncio
import logging
from datetime import datetime
import pytz

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from openai import AsyncOpenAI
import httpx
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
API_URL = os.getenv("API_URL", "http://backend:8000")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

logging.basicConfig(level=logging.INFO)
router = Router()

ai_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

TIMEZONES = [
    "UTC", "Europe/Moscow", "Europe/London", "Europe/Berlin",
    "Asia/Yekaterinburg", "Asia/Novosibirsk", "Asia/Vladivostok",
    "America/New_York", "America/Los_Angeles", "Asia/Dubai"
]


class Registration(StatesGroup):
    waiting_name = State()
    waiting_timezone = State()

class AddHabit(StatesGroup):
    waiting_name = State()
    waiting_time = State()

class ScheduleReport(StatesGroup):
    waiting_day = State()
    waiting_time = State()

class GetHabitAdvice(StatesGroup):
    waiting_habit_name = State()
    waiting_issue = State()

class GetRoleModelHabits(StatesGroup):
    waiting_role = State()

class GetSuggestions(StatesGroup):
    waiting_goal = State()


async def ask_ai(prompt: str) -> str:
    try:
        response = await ai_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        content = response.choices[0].message.content
        if content is None or content.strip() == "":
            return "🤖 AI couldn't generate a report right now. Don't worry — consistency beats perfection. Keep going! 💪"
        return content
    except Exception as e:
        return f"🤖 AI is taking a break: {str(e)}. But you shouldn't! Keep pushing forward 💪"


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    args = message.text.split()
    telegram_id = str(message.from_user.id)

    if len(args) > 1:
        code = args[1]
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{API_URL}/api/link-telegram", json={
                "code": code, "telegram_id": telegram_id
            })
        if r.status_code == 200:
            await message.answer(f"✅ Account linked! Welcome, {r.json().get('name', '')}!\n\nUse /help to see all commands.")
        else:
            await message.answer("❌ Invalid code. Try again.")
        return

    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_URL}/api/user-by-telegram/{telegram_id}")

    if r.status_code == 200:
        await message.answer(f"👋 Welcome back, {r.json().get('name', '')}!\n\nUse /help to see all commands.")
    else:
        await state.set_state(Registration.waiting_name)
        await message.answer("👋 Welcome to *Habit Tracker*!\n\nLet's set up your account. What's your name?", parse_mode="Markdown")


@router.message(Registration.waiting_name)
async def reg_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    buttons = [[InlineKeyboardButton(text=tz, callback_data=f"tz:{tz}")] for tz in TIMEZONES]
    await state.set_state(Registration.waiting_timezone)
    await message.answer("🌍 Select your timezone:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("tz:"))
async def reg_timezone(callback: CallbackQuery, state: FSMContext):
    tz = callback.data.split(":", 1)[1]
    data = await state.get_data()
    name = data.get("name", callback.from_user.first_name)
    telegram_id = str(callback.from_user.id)

    async with httpx.AsyncClient() as client:
        r = await client.post(f"{API_URL}/api/register-telegram", json={
            "telegram_id": telegram_id, "name": name, "timezone": tz,
        })

    await state.clear()
    if r.status_code == 200:
        await callback.message.edit_text(
            f"✅ Account created!\nName: *{name}*\nTimezone: *{tz}*\n\nAdd your first habit with /add",
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(f"❌ Error: {r.json().get('detail', 'Error')}")


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 *Habit Tracker — commands:*\n\n"
        "/add — add a new habit\n"
        "/done — mark habits as complete today\n"
        "/list — view all your habits\n"
        "/stats — streaks and weekly progress\n"
        "/report — AI weekly accountability report\n"
        "/schedule — set up automatic weekly report\n"
        "/delete — delete a habit\n"
        "/timezone — change your timezone\n"
        "/advise — get AI advice for a habit issue\n"
        "/rolemodel — find habits for a profession/role\n"
        "/suggest — get AI habit suggestions\n"
        "/insights — view your saved AI insights\n"
        "/help — show this message",
        parse_mode="Markdown"
    )


@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_URL}/api/user-by-telegram/{telegram_id}")
    if r.status_code != 200:
        await message.answer("❌ Please register first by sending /start")
        return
    await state.set_state(AddHabit.waiting_name)
    await message.answer("📝 What habit do you want to track?\n\nExamples: Running, Read 30 min, Meditation")


@router.message(AddHabit.waiting_name)
async def process_habit_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddHabit.waiting_time)
    await message.answer("⏰ Set a daily reminder time (e.g. 08:00)\n\nOr send /skip to add without reminder")


@router.message(AddHabit.waiting_time)
async def process_habit_time(message: Message, state: FSMContext):
    data = await state.get_data()
    telegram_id = str(message.from_user.id)
    reminder_time = None if message.text.strip() == "/skip" else message.text.strip()

    async with httpx.AsyncClient() as client:
        create_r = await client.post(
            f"{API_URL}/api/habits-by-telegram-create/{telegram_id}",
            json={"name": data["name"], "reminder_time": reminder_time}
        )

    if create_r.status_code == 200:
        reminder_text = f" — reminder at {reminder_time}" if reminder_time else ""
        await message.answer(f"✅ Habit added: *{data['name']}*{reminder_text}", parse_mode="Markdown")
    else:
        await message.answer(f"❌ Error: {create_r.text}")
    await state.clear()


@router.message(Command("list"))
async def cmd_list(message: Message):
    telegram_id = str(message.from_user.id)
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_URL}/api/habits-by-telegram/{telegram_id}")
    if r.status_code != 200:
        await message.answer("❌ Please register first by sending /start")
        return
    habits = r.json()
    if not habits:
        await message.answer("You have no habits yet. Add one with /add")
        return
    text = "📋 *Your habits:*\n\n"
    for h in habits:
        status = "✅" if h["done_today"] else "❌"
        text += f"{status} {h['name']}\n"
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("done"))
async def cmd_done(message: Message):
    telegram_id = str(message.from_user.id)
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_URL}/api/habits-by-telegram/{telegram_id}")
    if r.status_code != 200:
        await message.answer("❌ Please register first by sending /start")
        return
    habits = r.json()
    if not habits:
        await message.answer("No habits found. Add one with /add")
        return
    pending = [h for h in habits if not h["done_today"]]
    if not pending:
        await message.answer("🎉 All habits completed for today! Great job!")
        return
    buttons = [[InlineKeyboardButton(text=f"✅ {h['name']}", callback_data=f"complete:{h['id']}")] for h in pending]
    await message.answer("Which habit did you complete today?", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("complete:"))
async def callback_complete(callback: CallbackQuery):
    habit_id = callback.data.split(":")[1]
    telegram_id = str(callback.from_user.id)
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{API_URL}/api/complete-by-telegram/{telegram_id}/{habit_id}")
    if r.status_code == 200:
        streak = r.json().get("streak", 0)
        await callback.answer(f"✅ Done! Streak: {streak} days 🔥")
        await callback.message.edit_text(f"✅ Marked as complete! Current streak: *{streak} days* 🔥", parse_mode="Markdown")
    else:
        await callback.answer("❌ Error. Try again.")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    telegram_id = str(message.from_user.id)
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_URL}/api/stats/{telegram_id}")
    if r.status_code != 200:
        await message.answer("❌ Please register first by sending /start")
        return
    data = r.json()
    habits = data["habits"]
    if not habits:
        await message.answer("No habits yet. Add one with /add")
        return
    text = f"📊 *Stats for {data['name']}*\n\n"
    for h in habits:
        status = "✅" if h["done_today"] else "❌"
        fire = " 🔥" if h["streak"] >= 3 else ""
        text += f"{status} *{h['name']}*{fire}\n"
        text += f"   Streak: {h['streak']} days | This week: {h['week_completion']}\n\n"
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("timezone"))
async def cmd_timezone(message: Message):
    timezones = [
        ("🇷🇺 Moscow (UTC+3)", "Europe/Moscow"),
        ("🇷🇺 Yekaterinburg (UTC+5)", "Asia/Yekaterinburg"),
        ("🇷🇺 Novosibirsk (UTC+7)", "Asia/Novosibirsk"),
        ("🇷🇺 Vladivostok (UTC+10)", "Asia/Vladivostok"),
        ("🌍 UTC+0", "UTC"),
        ("🇩🇪 Berlin (UTC+1/2)", "Europe/Berlin"),
        ("🇦🇪 Dubai (UTC+4)", "Asia/Dubai"),
        ("🇺🇸 New York (UTC-5)", "America/New_York"),
        ("🇺🇸 Los Angeles (UTC-8)", "America/Los_Angeles"),
    ]
    buttons = [[InlineKeyboardButton(text=label, callback_data=f"settz:{tz}")] for label, tz in timezones]
    await message.answer("🌍 Select your timezone:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("settz:"))
async def callback_set_timezone(callback: CallbackQuery):
    tz = callback.data.split(":", 1)[1]
    telegram_id = str(callback.from_user.id)

    async with httpx.AsyncClient() as client:
        r = await client.patch(
            f"{API_URL}/api/user-timezone/{telegram_id}",
            json={"timezone": tz}
        )

    if r.status_code == 200:
        await callback.message.edit_text(f"✅ Timezone updated to *{tz}*", parse_mode="Markdown")
    else:
        await callback.answer("❌ Error. Try again.")


@router.message(Command("report"))
async def cmd_report(message: Message):
    telegram_id = str(message.from_user.id)
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_URL}/api/stats/{telegram_id}")
    if r.status_code != 200:
        await message.answer("❌ Please register first by sending /start")
        return
    data = r.json()
    habits = data["habits"]
    if not habits:
        await message.answer("No habits to analyze yet. Add some with /add")
        return

    await message.answer("🤖 Analyzing your habits... please wait")

    habits_text = "\n".join([
        f"- {h['name']}: streak {h['streak']} days, this week {h['week_completion']}, done today: {h['done_today']}"
        for h in habits
    ])

    # Fresh start fallback: when user did nothing this week, skip AI and send motivation directly
    total_this_week = sum(int(h["week_completion"].split("/")[0]) for h in habits)
    if total_this_week == 0:
        report = (
            f"🌱 *Week zero — and that's okay!*\n\n"
            f"Everyone starts somewhere. This week was a blank slate, which means next week you can build "
            f"something amazing. The hardest part isn't doing the habits — it's starting.\n\n"
            f"💡 *Tip:* Pick just ONE habit from your list and commit to doing it for 5 minutes a day. "
            f"Small wins compound into big results.\n\n"
            f"You've already taken the first step by setting up this tracker. Now let's make it count! 🚀"
        )
    else:
        prompt = f"""You are an accountability coach. Analyze this person's habit data and give a short motivational weekly report.

User: {data['name']}
Habits this week:
{habits_text}

Write a brief report (3-5 sentences) that:
1. Highlights their strongest habit
2. Points out which habit needs more attention
3. Gives one specific actionable tip
4. Ends with encouragement

Be direct, friendly, and specific. Use emojis."""

        report = await ask_ai(prompt)

    await message.answer(f"📊 *Weekly Report for {data['name']}*\n\n{report}", parse_mode="Markdown")


@router.message(Command("delete"))
async def cmd_delete(message: Message):
    telegram_id = str(message.from_user.id)
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_URL}/api/habits-by-telegram/{telegram_id}")
    if r.status_code != 200:
        await message.answer("❌ Please register first by sending /start")
        return
    habits = r.json()
    if not habits:
        await message.answer("No habits to delete.")
        return
    buttons = [[InlineKeyboardButton(text=f"🗑 {h['name']}", callback_data=f"delete:{h['id']}")] for h in habits]
    await message.answer("Which habit do you want to delete?", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("delete:"))
async def callback_delete(callback: CallbackQuery):
    habit_id = callback.data.split(":")[1]
    telegram_id = str(callback.from_user.id)
    async with httpx.AsyncClient() as client:
        r = await client.delete(f"{API_URL}/api/habits-by-telegram-delete/{telegram_id}/{habit_id}")
    if r.status_code == 200:
        await callback.answer("🗑 Deleted!")
        await callback.message.edit_text("✅ Habit deleted.")
    else:
        await callback.answer("❌ Error. Try again.")


@router.message(Command("schedule"))
async def cmd_schedule(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_URL}/api/user-by-telegram/{telegram_id}")
    if r.status_code != 200:
        await message.answer("❌ Please register first by sending /start")
        return

    days = [
        ("🟢 Monday", "monday"),
        ("🟢 Tuesday", "tuesday"),
        ("🟢 Wednesday", "wednesday"),
        ("🟢 Thursday", "thursday"),
        ("🟢 Friday", "friday"),
        ("🟢 Saturday", "saturday"),
        ("🟢 Sunday", "sunday"),
    ]
    buttons = [[InlineKeyboardButton(text=label, callback_data=f"rday:{day}")] for label, day in days]
    await message.answer(
        "📅 *Weekly Report Schedule*\n\n"
        "Choose a day of the week to receive your automatic AI report:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.set_state(ScheduleReport.waiting_day)


@router.callback_query(F.data.startswith("rday:"))
async def callback_report_day(callback: CallbackQuery, state: FSMContext):
    day = callback.data.split(":", 1)[1]
    await state.update_data(report_day=day)
    await state.set_state(ScheduleReport.waiting_time)
    await callback.message.edit_text(
        "⏰ Great! Now tell me what time you'd like to receive the report (e.g., 18:00 or 09:00):"
    )


@router.message(ScheduleReport.waiting_time)
async def process_report_time(message: Message, state: FSMContext):
    time_text = message.text.strip()
    # Validate time format
    try:
        hour, minute = map(int, time_text.split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except (ValueError, IndexError):
        await message.answer("❌ Invalid time format. Please use HH:MM (e.g., 18:00)")
        return

    data = await state.get_data()
    report_day = data.get("report_day")
    telegram_id = str(message.from_user.id)

    # Send to backend
    async with httpx.AsyncClient() as client:
        r = await client.patch(
            f"{API_URL}/api/user-report-schedule/{telegram_id}",
            json={"report_day": report_day, "report_time": time_text}
        )

    if r.status_code == 200:
        day_names = {
            "monday": "Monday",
            "tuesday": "Tuesday",
            "wednesday": "Wednesday",
            "thursday": "Thursday",
            "friday": "Friday",
            "saturday": "Saturday",
            "sunday": "Sunday",
        }
        day_name = day_names.get(report_day, report_day)
        await message.answer(
            f"✅ *Weekly Report Scheduled!*\n\n"
            f"📅 Day: *{day_name}*\n"
            f"⏰ Time: *{time_text}*\n\n"
            f"Every week at this time, I'll send you an AI-powered habit report. 💪",
            parse_mode="Markdown"
        )
    else:
        await message.answer("❌ Error saving schedule")

    await state.clear()


async def send_reminders(bot: Bot):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_URL}/api/all-users-habits")
    if r.status_code != 200:
        return
    for entry in r.json():
        telegram_id = entry["telegram_id"]
        timezone = entry.get("timezone", "UTC")
        habit_name = entry["habit_name"]
        reminder_time = entry["reminder_time"]
        done_today = entry["done_today"]
        if not reminder_time or not telegram_id:
            continue
        try:
            tz = pytz.timezone(timezone)
            now_local = datetime.now(tz)
            habit_hour, habit_min = map(int, reminder_time.split(":"))
            if now_local.hour == habit_hour and now_local.minute == habit_min and not done_today:
                await bot.send_message(telegram_id, f"⏰ Reminder: *{habit_name}*\nDon't forget to complete it today!", parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Reminder error: {e}")


async def ai_accountability_check(bot: Bot):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_URL}/api/all-users-stats")
    if r.status_code != 200:
        return
    for user_data in r.json():
        telegram_id = user_data.get("telegram_id")
        if not telegram_id:
            continue
        skipped = [h for h in user_data["habits"] if not h["done_today"] and h["streak"] > 0]
        if not skipped:
            continue
        skipped_names = ", ".join([h["name"] for h in skipped])
        prompt = f"""The user '{user_data['name']}' skipped these habits today: {skipped_names}.
Their streaks are at risk. Write a short (2-3 sentences) friendly but firm accountability message. Use emojis."""
        msg = await ask_ai(prompt)
        try:
            await bot.send_message(telegram_id, f"🤖 *Accountability check*\n\n{msg}", parse_mode="Markdown")
        except Exception as e:
            logging.error(f"AI check error: {e}")


async def send_weekly_reports(bot: Bot):
    """Send AI weekly reports to users based on their schedule"""
    # Get current day and hour
    now_utc = datetime.now(pytz.UTC)
    
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_URL}/api/users-with-report-schedule")
    if r.status_code != 200:
        return

    users_data = r.json()
    if not users_data:
        return

    # Day name mapping (Python weekday: 0=Monday)
    day_mapping = {
        0: "monday",
        1: "tuesday",
        2: "wednesday",
        3: "thursday",
        4: "friday",
        5: "saturday",
        6: "sunday"
    }
    
    current_day_name = day_mapping[now_utc.weekday()]
    current_hour = now_utc.hour

    for user_data in users_data:
        telegram_id = user_data.get("telegram_id")
        habits = user_data.get("habits", [])
        user_timezone = user_data.get("timezone", "UTC")
        
        if not telegram_id or not habits:
            continue

        # Check if it's the right day and time for this user
        try:
            tz = pytz.timezone(user_timezone)
            now_local = datetime.now(tz)
            user_day_name = day_mapping[now_local.weekday()]
            user_hour, user_min = map(int, user_data.get("report_time", "00:00").split(":"))
            
            # Only send if it's the right day and time (within the hour window)
            if user_day_name == current_day_name and now_local.hour == user_hour and now_local.minute < 5:
                await send_report_to_user(bot, user_data)
        except Exception as e:
            logging.error(f"Error checking schedule for {telegram_id}: {e}")


async def send_report_to_user(bot: Bot, user_data: dict):
    """Send a weekly report to a single user"""
    telegram_id = user_data.get("telegram_id")
    habits = user_data.get("habits", [])

    try:
        await bot.send_message(telegram_id, "🤖 Generating your weekly report... please wait a moment")

        habits_text = "\n".join([
            f"- {h['name']}: streak {h['streak']} days, this week {h['week_completion']}, done today: {h['done_today']}"
            for h in habits
        ])

        # Fresh start fallback
        total_this_week = sum(int(h["week_completion"].split("/")[0]) for h in habits)
        if total_this_week == 0:
            report = (
                f"🌱 *Week zero — and that's okay!*\n\n"
                f"Everyone starts somewhere. This week was a blank slate, which means next week you can build "
                f"something amazing. The hardest part isn't doing the habits — it's starting.\n\n"
                f"💡 *Tip:* Pick just ONE habit from your list and commit to doing it for 5 minutes a day. "
                f"Small wins compound into big results.\n\n"
                f"You've already taken the first step by setting up this tracker. Now let's make it count! 🚀"
            )
        else:
            prompt = f"""You are an accountability coach. Analyze this person's habit data and give a short motivational weekly report.

User: {user_data['name']}
Habits this week:
{habits_text}

Write a brief report (3-5 sentences) that:
1. Highlights their strongest habit
2. Points out which habit needs more attention
3. Gives one specific actionable tip
4. Ends with encouragement

Be direct, friendly, and specific. Use emojis."""

            report = await ask_ai(prompt)

        await bot.send_message(
            telegram_id,
            f"📊 *Weekly Report for {user_data['name']}*\n\n{report}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Weekly report error for {telegram_id}: {e}")


# ---------- New AI commands ----------

@router.message(Command("advise"))
async def cmd_advise(message: Message, state: FSMContext):
    """Get AI advice for a specific habit issue"""
    telegram_id = str(message.from_user.id)
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_URL}/api/user-by-telegram/{telegram_id}")
    if r.status_code != 200:
        await message.answer("❌ Please register first by sending /start")
        return

    await state.set_state(GetHabitAdvice.waiting_habit_name)
    await message.answer(
        "🤖 *Habit Advisor*\n\n"
        "What habit do you need advice about?\n\n"
        "Example: Reading, Exercise, Meditation",
        parse_mode="Markdown"
    )


@router.message(GetHabitAdvice.waiting_habit_name)
async def process_advice_habit_name(message: Message, state: FSMContext):
    await state.update_data(habit_name=message.text.strip())
    await state.set_state(GetHabitAdvice.waiting_issue)
    await message.answer(
        "What's the issue with this habit?\n\n"
        "Examples:\n"
        "• Not enough time\n"
        "• Became too easy\n"
        "• Lost motivation\n"
        "• Too difficult\n"
        "• Keep forgetting"
    )


@router.message(GetHabitAdvice.waiting_issue)
async def process_advice_issue(message: Message, state: FSMContext):
    data = await state.get_data()
    habit_name = data["habit_name"]
    issue = message.text.strip()
    telegram_id = str(message.from_user.id)

    await message.answer("🤖 Analyzing your habit and generating advice... Please wait a moment.")

    timeout = httpx.Timeout(120.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(f"{API_URL}/api/bot/ai-habit-advice", json={
            "telegram_id": telegram_id,
            "habit_name": habit_name,
            "issue": issue
        })

    await state.clear()
    if r.status_code == 200:
        insight = r.json()
        habit_name_display = insight.get('habit_name', habit_name)
        await message.answer(
            f"💡 *Advice for: {habit_name_display}*\n\n"
            f"{insight['content']}\n\n"
            f"_This insight has been saved to your profile. Use /insights to view it later._",
            parse_mode="Markdown"
        )
    else:
        await message.answer(f"❌ Error getting advice: {r.text}")


@router.message(Command("rolemodel"))
async def cmd_rolemodel(message: Message, state: FSMContext):
    """Get habit suggestions based on a role model or profession"""
    telegram_id = str(message.from_user.id)
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_URL}/api/user-by-telegram/{telegram_id}")
    if r.status_code != 200:
        await message.answer("❌ Please register first by sending /start")
        return

    await state.set_state(GetRoleModelHabits.waiting_role)
    await message.answer(
        "🎭 *Role Model Habits*\n\n"
        "Tell me a profession or describe a type of person whose habits you want to adopt.\n\n"
        "Examples:\n"
        "• Software Engineer\n"
        "• Professional Athlete\n"
        "• Successful Entrepreneur\n"
        "• Creative Writer\n"
        "• Research Scientist",
        parse_mode="Markdown"
    )


@router.message(GetRoleModelHabits.waiting_role)
async def process_rolemodel_role(message: Message, state: FSMContext):
    role = message.text.strip()
    telegram_id = str(message.from_user.id)

    await message.answer("🤖 Generating profession-based habit recommendations... Please wait.")

    # Get existing habits
    timeout = httpx.Timeout(120.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        habits_resp = await client.get(f"{API_URL}/api/habits-by-telegram/{telegram_id}")
        existing_habits = [h["name"] for h in habits_resp.json()] if habits_resp.status_code == 200 else []

        r = await client.post(f"{API_URL}/api/bot/ai-role-model-habits", json={
            "telegram_id": telegram_id,
            "role_or_profession": role,
            "existing_habits": existing_habits
        })

    await state.clear()
    if r.status_code == 200:
        insight = r.json()
        await message.answer(
            f"🎯 *Habits for: {insight.get('context', role)}*\n\n"
            f"{insight['content']}\n\n"
            f"_This insight has been saved. Use /insights to view later._",
            parse_mode="Markdown"
        )
    else:
        await message.answer(f"❌ Error: {r.text}")


@router.message(Command("suggest"))
async def cmd_suggest(message: Message, state: FSMContext):
    """Get general AI habit suggestions"""
    telegram_id = str(message.from_user.id)
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_URL}/api/user-by-telegram/{telegram_id}")
    if r.status_code != 200:
        await message.answer("❌ Please register first by sending /start")
        return

    await state.set_state(GetSuggestions.waiting_goal)
    await message.answer(
        "🌟 *Habit Suggestions*\n\n"
        "What's your goal? I'll suggest habits that fit.\n\n"
        "Examples:\n"
        "• Become more productive\n"
        "• Get in better shape\n"
        "• Reduce stress\n"
        "• Learn faster\n\n"
        "Or send /any for general suggestions.",
        parse_mode="Markdown"
    )


@router.message(GetSuggestions.waiting_goal)
async def process_suggest_goal(message: Message, state: FSMContext):
    goal = message.text.strip()
    telegram_id = str(message.from_user.id)

    if goal.lower() == "/any":
        goal = None

    await message.answer("🤖 Generating personalized habit suggestions... Please wait.")

    timeout = httpx.Timeout(120.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        payload = {"telegram_id": telegram_id, "goal": goal} if goal else {"telegram_id": telegram_id}
        r = await client.post(f"{API_URL}/api/bot/ai-suggest-habits", json=payload)

    await state.clear()
    if r.status_code == 200:
        insight = r.json()
        await message.answer(
            f"✨ *Suggestions for: {insight.get('context', 'general improvement')}*\n\n"
            f"{insight['content']}\n\n"
            f"_Saved to your profile. Use /insights to review._",
            parse_mode="Markdown"
        )
    else:
        await message.answer(f"❌ Error: {r.text}")


@router.message(Command("insights"))
async def cmd_insights(message: Message):
    """View saved AI insights"""
    telegram_id = str(message.from_user.id)
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_URL}/api/user-by-telegram/{telegram_id}")
    if r.status_code != 200:
        await message.answer("❌ Please register first by sending /start")
        return

    await message.answer("📚 Loading your insights...")

    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(f"{API_URL}/api/bot/ai-insights/{telegram_id}")

    if r.status_code != 200:
        await message.answer("❌ Error loading insights.")
        return

    insights = r.json()
    if not insights:
        await message.answer(
            "📭 No insights yet.\n\n"
            "Use these commands to get AI-powered insights:\n"
            "• /advise — advice on a specific habit\n"
            "• /rolemodel — habits for a profession\n"
            "• /suggest — general habit suggestions\n"
            "• /report — weekly accountability report"
        )
        return

    type_emoji = {
        "habit_advice": "💡",
        "role_model": "🎭",
        "suggest_habits": "✨",
        "weekly_report": "📊",
    }

    # Show last 5 insights
    for insight in insights[:5]:
        emoji = type_emoji.get(insight["insight_type"], "🤖")
        context = insight.get("context", "")
        habit_name = insight.get("habit_name", "")
        
        header = f"{emoji} *{insight['insight_type'].replace('_', ' ').title()}*"
        if habit_name:
            header += f" — {habit_name}"
        if context:
            header += f"\n📌 {context}"
        
        await message.answer(
            f"{header}\n\n{insight['content']}",
            parse_mode="Markdown"
        )

    if len(insights) > 5:
        await message.answer(f"📋 Showing 5 of {len(insights)} insights. Older ones available in the web dashboard.")


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_reminders, "cron", minute="*", args=[bot])
    scheduler.add_job(ai_accountability_check, "cron", hour=21, minute=0, args=[bot])
    scheduler.add_job(send_weekly_reports, "cron", minute="*/5", args=[bot])  # Check every 5 minutes
    scheduler.start()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())