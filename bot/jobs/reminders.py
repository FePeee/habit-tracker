import logging
from datetime import datetime

import pytz
from aiogram import Bot

from api_client import api

logger = logging.getLogger(__name__)


def _parse_reminder_clock(reminder_time: str) -> tuple[int, int] | None:
    """
    Parse stored reminder time. Accepts HH:MM (bot) or HH:MM:SS (some browsers / DB).
    Returns (hour, minute) or None if invalid.
    """
    if not reminder_time:
        return None
    s = str(reminder_time).strip()
    parts = s.split(":")
    if len(parts) < 2:
        return None
    try:
        h = int(parts[0])
        m = int(parts[1])
        if 0 <= h <= 23 and 0 <= m <= 59:
            return h, m
    except ValueError:
        pass
    return None


async def send_reminders(bot: Bot):
    try:
        entries = await api.get_all_users_habits()
    except Exception as e:
        logger.error("Failed to fetch habits for reminders: %s", e)
        return

    if not entries:
        return

    for entry in entries:
        telegram_id = entry.get("telegram_id")
        timezone = entry.get("timezone") or "UTC"
        habit_name = entry.get("habit_name", "")
        reminder_time = entry.get("reminder_time")
        done_today = entry.get("done_today", False)

        if not reminder_time or not telegram_id:
            continue

        parsed = _parse_reminder_clock(reminder_time)
        if parsed is None:
            logger.warning(
                "Skipping reminder: invalid reminder_time %r for telegram_id=%s habit=%r",
                reminder_time,
                telegram_id,
                habit_name,
            )
            continue

        habit_hour, habit_min = parsed

        try:
            tz = pytz.timezone(timezone.strip() or "UTC")
        except Exception as e:
            logger.warning("Invalid timezone %r for telegram_id=%s: %s", timezone, telegram_id, e)
            continue

        try:
            now_local = datetime.now(tz)
            if now_local.hour != habit_hour or now_local.minute != habit_min:
                continue
            if done_today:
                continue

            await bot.send_message(
                int(telegram_id),
                f"Reminder: {habit_name}\nDon't forget to complete it today!",
            )
            logger.info(
                "Sent reminder to telegram_id=%s for habit=%r at %02d:%02d %s",
                telegram_id,
                habit_name,
                habit_hour,
                habit_min,
                timezone,
            )
        except Exception as e:
            logger.error("Reminder error for %s: %s", telegram_id, e)
