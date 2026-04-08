import logging
from datetime import datetime

import pytz
from aiogram import Bot

from ai import ask_ai
from api_client import api

logger = logging.getLogger(__name__)


async def ai_accountability_check(bot: Bot):
    try:
        all_stats = await api.get_all_users_stats()
    except Exception as e:
        logger.error("Failed to fetch stats for accountability: %s", e)
        return

    for user_data in all_stats:
        telegram_id = user_data.get("telegram_id")
        if not telegram_id:
            continue

        skipped = [h for h in user_data["habits"] if not h["done_today"] and h["streak"] > 0]
        if not skipped:
            continue

        skipped_names = ", ".join(h["name"] for h in skipped)
        prompt = (
            f"The user '{user_data['name']}' skipped these habits today: {skipped_names}. "
            f"Their streaks are at risk. Write a short (2-3 sentences) friendly but firm "
            f"accountability message. Use emojis."
        )
        msg = await ask_ai(prompt)
        try:
            await bot.send_message(int(telegram_id), f"Accountability check\n\n{msg}")
        except Exception as e:
            logger.error("AI check error for %s: %s", telegram_id, e)
