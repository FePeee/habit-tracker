from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
from database import get_db
from services import calculate_streak, get_active_habits, normalize_reminder_time

router = APIRouter(prefix="/api", tags=["bulk"])


@router.get("/users-with-report-schedule")
def get_users_with_report_schedule(db: Session = Depends(get_db)):
    users = (
        db.query(models.User)
        .filter(
            models.User.telegram_id != None,
            models.User.report_day != None,
            models.User.report_time != None,
        )
        .all()
    )
    today = date.today()
    week_start = today - timedelta(days=6)
    result = []
    for user in users:
        habits = get_active_habits(user.id, db)
        habits_data = []
        for h in habits:
            done_today = any(c.date == today for c in h.completions)
            week_done = sum(1 for c in h.completions if week_start <= c.date <= today)
            habits_data.append({
                "id": h.id,
                "name": h.name,
                "streak": calculate_streak(h),
                "done_today": done_today,
                "week_completion": f"{week_done}/7",
            })
        result.append({
            "telegram_id": user.telegram_id,
            "name": user.name,
            "timezone": user.timezone,
            "report_day": user.report_day,
            "report_time": user.report_time,
            "habits": habits_data,
        })
    return result


@router.get("/all-users-habits")
def get_all_users_habits(db: Session = Depends(get_db)):
    users = db.query(models.User).filter(models.User.telegram_id != None).all()
    today = date.today()
    result = []
    for user in users:
        habits = get_active_habits(user.id, db)
        for h in habits:
            if not h.reminder_time:
                continue
            done_today = any(c.date == today for c in h.completions)
            rt = normalize_reminder_time(h.reminder_time) or h.reminder_time
            result.append({
                "telegram_id": user.telegram_id,
                "timezone": user.timezone,
                "habit_name": h.name,
                "reminder_time": rt,
                "done_today": done_today,
            })
    return result


@router.get("/all-users-stats")
def get_all_users_stats(db: Session = Depends(get_db)):
    users = db.query(models.User).filter(models.User.telegram_id != None).all()
    today = date.today()
    week_start = today - timedelta(days=6)
    result = []
    for user in users:
        habits = get_active_habits(user.id, db)
        habits_data = []
        for h in habits:
            done_today = any(c.date == today for c in h.completions)
            week_done = sum(1 for c in h.completions if week_start <= c.date <= today)
            habits_data.append({
                "id": h.id,
                "name": h.name,
                "streak": calculate_streak(h),
                "done_today": done_today,
                "week_completion": f"{week_done}/7",
            })
        result.append({
            "telegram_id": user.telegram_id,
            "name": user.name,
            "habits": habits_data,
        })
    return result
