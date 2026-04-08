import logging
from datetime import datetime

import pytz
from aiogram import Bot

from ai import ask_ai
from api_client import api

logger = logging.getLogger(__name__)

DAY_MAPPING = {
    0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday",
    4: "friday", 5: "saturday", 6: "sunday",
}

_sent_cache: dict[str, str] = {}


async def send_weekly_reports(bot: Bot):
    try:
        users_data = await api.get_users_with_report_schedule()
    except Exception as e:
        logger.error("Failed to fetch report schedule: %s", e)
        return

    for user_data in users_data:
        telegram_id = user_data.get("telegram_id")
        habits = user_data.get("habits", [])
        user_timezone = user_data.get("timezone", "UTC")
        report_day = user_data.get("report_day")
        report_time = user_data.get("report_time")

        if not telegram_id or not habits or not report_day or not report_time:
            continue

        try:
            tz = pytz.timezone(user_timezone)
            now_local = datetime.now(tz)
            user_day_name = DAY_MAPPING[now_local.weekday()]
            user_hour, user_min = map(int, report_time.split(":"))

            if user_day_name != report_day or now_local.hour != user_hour or now_local.minute >= 5:
                continue

            cache_key = f"{telegram_id}:{now_local.date()}"
            if _sent_cache.get(telegram_id) == cache_key:
                continue
            _sent_cache[telegram_id] = cache_key

            await _send_report_to_user(bot, user_data)
        except Exception as e:
            logger.error("Error checking schedule for %s: %s", telegram_id, e)


async def _send_report_to_user(bot: Bot, user_data: dict):
    telegram_id = user_data.get("telegram_id")
    habits = user_data.get("habits", [])

    try:
        await bot.send_message(int(telegram_id), "Generating your weekly report... please wait a moment")

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
            int(telegram_id),
            f"Weekly Report for {user_data['name']}\n\n{report}",
        )
    except Exception as e:
        logger.error("Weekly report error for %s: %s", telegram_id, e)
