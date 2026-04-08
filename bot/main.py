import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN, OPENROUTER_API_KEY
from handlers import start, help, habits, stats, schedule, ai_commands
from jobs.reminders import send_reminders
from jobs.accountability import ai_accountability_check
from jobs.weekly_report import send_weekly_reports

logging.basicConfig(level=logging.INFO)

if OPENROUTER_API_KEY:
    logging.info("OpenRouter API key loaded (%d characters)", len(OPENROUTER_API_KEY))
else:
    logging.warning(
        "OPENROUTER_API_KEY is empty -- AI commands will not work "
        "until you set it in .env and recreate the bot container"
    )


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Start or link account"),
        BotCommand(command="add", description="Add a new habit"),
        BotCommand(command="done", description="Mark habit as complete"),
        BotCommand(command="list", description="View all habits"),
        BotCommand(command="stats", description="View streaks & progress"),
        BotCommand(command="report", description="AI weekly report"),
        BotCommand(command="schedule", description="Schedule weekly reports"),
        BotCommand(command="delete", description="Delete a habit"),
        BotCommand(command="timezone", description="Change timezone"),
        BotCommand(command="advise", description="AI advice for a habit"),
        BotCommand(command="rolemodel", description="Habits for a profession"),
        BotCommand(command="suggest", description="AI habit suggestions"),
        BotCommand(command="insights", description="View saved AI insights"),
        BotCommand(command="help", description="Show all commands"),
    ]
    await bot.set_my_commands(commands)


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(help.router)
    dp.include_router(habits.router)
    dp.include_router(stats.router)
    dp.include_router(schedule.router)
    dp.include_router(ai_commands.router)

    await set_bot_commands(bot)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_reminders, "cron", minute="*", args=[bot])
    scheduler.add_job(ai_accountability_check, "cron", hour=21, minute=0, args=[bot])
    scheduler.add_job(send_weekly_reports, "cron", minute="*/5", args=[bot])
    scheduler.start()

    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
