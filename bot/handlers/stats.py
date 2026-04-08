from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from ai import ask_ai
from api_client import api

router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    telegram_id = str(message.from_user.id)
    data = await api.get_stats(telegram_id)
    if data is None:
        await message.answer("Please register first by sending /start")
        return
    habits = data["habits"]
    if not habits:
        await message.answer("No habits yet. Add one with /add")
        return
    text = f"Stats for {data['name']}\n\n"
    for h in habits:
        done = "[x]" if h["done_today"] else "[ ]"
        fire = " (streak!)" if h["streak"] >= 3 else ""
        text += f"{done} {h['name']}{fire}\n"
        text += f"   Streak: {h['streak']} days | This week: {h['week_completion']}\n\n"
    await message.answer(text)


@router.message(Command("report"))
async def cmd_report(message: Message):
    telegram_id = str(message.from_user.id)
    data = await api.get_stats(telegram_id)
    if data is None:
        await message.answer("Please register first by sending /start")
        return
    habits = data["habits"]
    if not habits:
        await message.answer("No habits to analyze yet. Add some with /add")
        return

    await message.answer("Analyzing your habits... please wait")

    habits_text = "\n".join([
        f"- {h['name']}: streak {h['streak']} days, this week {h['week_completion']}, done today: {h['done_today']}"
        for h in habits
    ])

    total_this_week = sum(int(h["week_completion"].split("/")[0]) for h in habits)
    if total_this_week == 0:
        report = (
            "Week zero -- and that's okay!\n\n"
            "Everyone starts somewhere. This week was a blank slate, which means next week "
            "you can build something amazing. The hardest part isn't doing the habits -- it's starting.\n\n"
            "Tip: Pick just ONE habit from your list and commit to doing it for 5 minutes a day. "
            "Small wins compound into big results.\n\n"
            "You've already taken the first step by setting up this tracker. Now let's make it count!"
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

    await message.answer(f"Weekly Report for {data['name']}\n\n{report}")
