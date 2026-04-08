import secrets
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from auth import hash_password
from database import get_db
from schemas import HabitCreate, HabitOut, LinkTelegram
from services import (
    get_user_by_telegram,
    get_active_habits,
    habit_to_out,
    complete_habit_for_user,
    delete_habit_for_user,
    build_stats,
    normalize_reminder_time,
)

router = APIRouter(prefix="/api", tags=["telegram"])


@router.patch("/user-timezone/{telegram_id}")
def update_timezone(telegram_id: str, data: dict, db: Session = Depends(get_db)):
    user = get_user_by_telegram(telegram_id, db)
    user.timezone = data.get("timezone", "UTC")
    db.commit()
    return {"message": "Timezone updated", "timezone": user.timezone}


@router.patch("/user-report-schedule/{telegram_id}")
def update_report_schedule(telegram_id: str, data: dict, db: Session = Depends(get_db)):
    user = get_user_by_telegram(telegram_id, db)
    user.report_day = data.get("report_day", user.report_day)
    user.report_time = data.get("report_time", user.report_time)
    db.commit()
    return {
        "message": "Report schedule updated",
        "report_day": user.report_day,
        "report_time": user.report_time,
    }


@router.post("/register-telegram")
def register_telegram(data: dict, db: Session = Depends(get_db)):
    telegram_id = data.get("telegram_id")
    name = data.get("name")
    timezone = data.get("timezone", "UTC")

    existing = db.query(models.User).filter(models.User.telegram_id == telegram_id).first()
    if existing:
        return {"message": "Already registered", "name": existing.name}

    user = models.User(
        email=f"tg_{telegram_id}@habittracker.bot",
        hashed_password=hash_password(secrets.token_hex(16)),
        name=name,
        telegram_id=telegram_id,
        timezone=timezone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Registered", "name": user.name}


@router.post("/link-telegram")
def link_telegram(data: LinkTelegram, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.link_code == data.code).first()
    if not user:
        raise HTTPException(status_code=404, detail="Invalid code")

    existing = db.query(models.User).filter(models.User.telegram_id == data.telegram_id).first()
    if existing:
        if existing.id == user.id:
            return {"message": "Already linked", "name": user.name}
        if existing.email.endswith("@habittracker.bot"):
            for habit in db.query(models.Habit).filter(models.Habit.user_id == existing.id).all():
                habit.user_id = user.id
            for insight in (
                db.query(models.AIInsight).filter(models.AIInsight.user_id == existing.id).all()
            ):
                insight.user_id = user.id
            user.timezone = existing.timezone or user.timezone
            user.report_day = existing.report_day or user.report_day
            user.report_time = existing.report_time or user.report_time
            existing.telegram_id = None
            db.flush()
            db.delete(existing)
            db.flush()
        else:
            raise HTTPException(status_code=400, detail="Telegram already linked to another account")

    user.telegram_id = data.telegram_id
    user.link_code = None
    db.commit()
    return {"message": "Linked successfully", "name": user.name}


@router.get("/user-by-telegram/{telegram_id}")
def get_user_by_telegram_route(telegram_id: str, db: Session = Depends(get_db)):
    user = get_user_by_telegram(telegram_id, db)
    return {"id": user.id, "name": user.name, "telegram_id": user.telegram_id}


@router.get("/stats/{telegram_id}")
def get_stats_by_telegram(telegram_id: str, db: Session = Depends(get_db)):
    user = get_user_by_telegram(telegram_id, db)
    return build_stats(user, db)


@router.get("/habits-by-telegram/{telegram_id}")
def get_habits_by_telegram(telegram_id: str, db: Session = Depends(get_db)):
    user = get_user_by_telegram(telegram_id, db)
    habits = get_active_habits(user.id, db)
    today = date.today()
    return [
        {"id": h.id, "name": h.name, "done_today": any(c.date == today for c in h.completions)}
        for h in habits
    ]


@router.post("/habits-by-telegram-create/{telegram_id}", response_model=HabitOut)
def create_habit_by_telegram(
    telegram_id: str, data: HabitCreate, db: Session = Depends(get_db)
):
    user = get_user_by_telegram(telegram_id, db)
    habit = models.Habit(
        user_id=user.id,
        name=data.name,
        reminder_time=normalize_reminder_time(data.reminder_time),
    )
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return HabitOut(
        id=habit.id, name=habit.name, reminder_time=habit.reminder_time,
        is_active=habit.is_active, streak=0, done_today=False,
    )


@router.delete("/habits-by-telegram-delete/{telegram_id}/{habit_id}")
def delete_habit_by_telegram(telegram_id: str, habit_id: int, db: Session = Depends(get_db)):
    user = get_user_by_telegram(telegram_id, db)
    return delete_habit_for_user(user, habit_id, db)


@router.post("/complete-by-telegram/{telegram_id}/{habit_id}")
def complete_by_telegram(telegram_id: str, habit_id: int, db: Session = Depends(get_db)):
    user = get_user_by_telegram(telegram_id, db)
    return complete_habit_for_user(user, habit_id, db)
