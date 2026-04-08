from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Habit Tracker -- commands:\n\n"
        "/add -- add a new habit\n"
        "/done -- mark habits as complete today\n"
        "/list -- view all your habits\n"
        "/stats -- streaks and weekly progress\n"
        "/report -- AI weekly accountability report\n"
        "/schedule -- set up automatic weekly report\n"
        "/delete -- delete a habit\n"
        "/timezone -- change your timezone\n"
        "/advise -- get AI advice for a habit issue\n"
        "/rolemodel -- find habits for a profession/role\n"
        "/suggest -- get AI habit suggestions\n"
        "/insights -- view your saved AI insights\n"
        "/help -- show this message"
    )
