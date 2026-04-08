import logging

import httpx
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from api_client import api

logger = logging.getLogger(__name__)
router = Router()


class GetHabitAdvice(StatesGroup):
    waiting_habit_name = State()
    waiting_issue = State()


class GetRoleModelHabits(StatesGroup):
    waiting_role = State()


class GetSuggestions(StatesGroup):
    waiting_goal = State()


async def _require_registration(message: Message) -> str | None:
    telegram_id = str(message.from_user.id)
    user = await api.get_user(telegram_id)
    if not user:
        await message.answer("Please register first by sending /start")
        return None
    return telegram_id


# ---- /advise ----

@router.message(Command("advise"))
async def cmd_advise(message: Message, state: FSMContext):
    if not await _require_registration(message):
        return
    await state.set_state(GetHabitAdvice.waiting_habit_name)
    await message.answer(
        "Habit Advisor\n\n"
        "What habit do you need advice about?\n\n"
        "Example: Reading, Exercise, Meditation"
    )


@router.message(GetHabitAdvice.waiting_habit_name)
async def process_advice_habit_name(message: Message, state: FSMContext):
    await state.update_data(habit_name=message.text.strip())
    await state.set_state(GetHabitAdvice.waiting_issue)
    await message.answer(
        "What's the issue with this habit?\n\n"
        "Examples:\n"
        "- Not enough time\n"
        "- Became too easy\n"
        "- Lost motivation\n"
        "- Too difficult\n"
        "- Keep forgetting"
    )


@router.message(GetHabitAdvice.waiting_issue)
async def process_advice_issue(message: Message, state: FSMContext):
    data = await state.get_data()
    habit_name = data["habit_name"]
    issue = message.text.strip()
    telegram_id = str(message.from_user.id)

    await message.answer("Analyzing your habit and generating advice... Please wait a moment.")

    try:
        r = await api.bot_ai_advice(telegram_id, habit_name, issue)
    except (httpx.ReadTimeout, httpx.HTTPError) as e:
        await state.clear()
        logger.warning("Advice request failed: %s", e)
        await message.answer("AI request timed out. Please try again in a minute.")
        return

    await state.clear()
    if r.status_code == 200:
        insight = r.json()
        await message.answer(
            f"Advice for: {insight.get('habit_name', habit_name)}\n\n"
            f"{insight['content']}\n\n"
            f"This insight has been saved to your profile. Use /insights to view it later."
        )
    else:
        await message.answer("Error getting advice. Please try again.")


# ---- /rolemodel ----

@router.message(Command("rolemodel"))
async def cmd_rolemodel(message: Message, state: FSMContext):
    if not await _require_registration(message):
        return
    await state.set_state(GetRoleModelHabits.waiting_role)
    await message.answer(
        "Role Model Habits\n\n"
        "Tell me a profession or describe a type of person whose habits you want to adopt.\n\n"
        "Examples:\n"
        "- Software Engineer\n"
        "- Professional Athlete\n"
        "- Successful Entrepreneur\n"
        "- Creative Writer\n"
        "- Research Scientist"
    )


@router.message(GetRoleModelHabits.waiting_role)
async def process_rolemodel_role(message: Message, state: FSMContext):
    role = message.text.strip()
    telegram_id = str(message.from_user.id)

    await message.answer("Generating profession-based habit recommendations... Please wait.")

    try:
        habits = await api.get_habits(telegram_id)
        existing = [h["name"] for h in habits] if habits else []
        r = await api.bot_ai_rolemodel(telegram_id, role, existing)
    except (httpx.ReadTimeout, httpx.HTTPError) as e:
        await state.clear()
        logger.warning("Rolemodel request failed: %s", e)
        await message.answer("AI request timed out. Please try again in a minute.")
        return

    await state.clear()
    if r.status_code == 200:
        insight = r.json()
        await message.answer(
            f"Habits for: {insight.get('context', role)}\n\n"
            f"{insight['content']}\n\n"
            f"This insight has been saved. Use /insights to view later."
        )
    else:
        await message.answer("Error. Please try again.")


# ---- /suggest ----

@router.message(Command("suggest"))
async def cmd_suggest(message: Message, state: FSMContext):
    if not await _require_registration(message):
        return
    await state.set_state(GetSuggestions.waiting_goal)
    await message.answer(
        "Habit Suggestions\n\n"
        "What's your goal? I'll suggest habits that fit.\n\n"
        "Examples:\n"
        "- Become more productive\n"
        "- Get in better shape\n"
        "- Reduce stress\n"
        "- Learn faster\n\n"
        "Or send /any for general suggestions."
    )


@router.message(GetSuggestions.waiting_goal)
async def process_suggest_goal(message: Message, state: FSMContext):
    goal = message.text.strip()
    telegram_id = str(message.from_user.id)
    if goal.lower() == "/any":
        goal = None

    await message.answer("Generating personalized habit suggestions... Please wait.")

    try:
        r = await api.bot_ai_suggest(telegram_id, goal)
    except (httpx.ReadTimeout, httpx.HTTPError) as e:
        await state.clear()
        logger.warning("Suggest request failed: %s", e)
        await message.answer("AI request timed out. Please try again in a minute.")
        return

    await state.clear()
    if r.status_code == 200:
        insight = r.json()
        await message.answer(
            f"Suggestions for: {insight.get('context', 'general improvement')}\n\n"
            f"{insight['content']}\n\n"
            f"Saved to your profile. Use /insights to review."
        )
    else:
        await message.answer("Error. Please try again.")


# ---- /insights ----

@router.message(Command("insights"))
async def cmd_insights(message: Message):
    telegram_id = str(message.from_user.id)
    user = await api.get_user(telegram_id)
    if not user:
        await message.answer("Please register first by sending /start")
        return

    insights = await api.bot_ai_insights(telegram_id)
    if not insights:
        await message.answer(
            "No insights yet.\n\n"
            "Use these commands to get AI-powered insights:\n"
            "- /advise -- advice on a specific habit\n"
            "- /rolemodel -- habits for a profession\n"
            "- /suggest -- general habit suggestions\n"
            "- /report -- weekly accountability report"
        )
        return

    type_emoji = {
        "habit_advice": "Advice",
        "role_model": "Role Model",
        "suggest_habits": "Suggestions",
        "weekly_report": "Weekly Report",
    }

    for insight in insights[:5]:
        label = type_emoji.get(insight["insight_type"], "Insight")
        context = insight.get("context", "")
        habit_name = insight.get("habit_name", "")

        header = label
        if habit_name:
            header += f" -- {habit_name}"
        if context:
            header += f"\n{context}"

        await message.answer(f"{header}\n\n{insight['content']}")

    if len(insights) > 5:
        await message.answer(f"Showing 5 of {len(insights)} insights. Older ones available in the web dashboard.")
