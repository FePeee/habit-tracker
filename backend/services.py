from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

import models
from schemas import HabitOut, AIInsightOut


def normalize_reminder_time(value: Optional[str]) -> Optional[str]:
    """Store HH:MM only; accept HH:MM:SS from HTML time inputs."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    parts = s.split(":")
    if len(parts) < 2:
        return None
    try:
        h, m = int(parts[0]), int(parts[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            return None
        return f"{h:02d}:{m:02d}"
    except ValueError:
        return None


def calculate_streak(habit: models.Habit) -> int:
    completion_dates = sorted({c.date for c in habit.completions}, reverse=True)
    if not completion_dates:
        return 0
    streak = 0
    check_date = date.today()
    for d in completion_dates:
        if d == check_date:
            streak += 1
            check_date -= timedelta(days=1)
        elif d == check_date - timedelta(days=1):
            check_date = d
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    return streak


def habit_to_out(h: models.Habit) -> HabitOut:
    today = date.today()
    done_today = any(c.date == today for c in h.completions)
    return HabitOut(
        id=h.id,
        name=h.name,
        reminder_time=h.reminder_time,
        is_active=h.is_active,
        streak=calculate_streak(h),
        done_today=done_today,
    )


def get_user_by_telegram(telegram_id: str, db: Session) -> models.User:
    from fastapi import HTTPException

    user = db.query(models.User).filter(models.User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_active_habits(user_id: int, db: Session) -> list[models.Habit]:
    return (
        db.query(models.Habit)
        .filter(models.Habit.user_id == user_id, models.Habit.is_active == True)
        .all()
    )


def build_stats(user: models.User, db: Session) -> dict:
    habits = get_active_habits(user.id, db)
    today = date.today()
    week_start = today - timedelta(days=6)
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
    return {"name": user.name, "habits": habits_data}


def complete_habit_for_user(
    user: models.User, habit_id: int, db: Session
) -> dict:
    from fastapi import HTTPException

    habit = (
        db.query(models.Habit)
        .filter(models.Habit.id == habit_id, models.Habit.user_id == user.id)
        .first()
    )
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    today = date.today()
    existing = (
        db.query(models.Completion)
        .filter(models.Completion.habit_id == habit_id, models.Completion.date == today)
        .first()
    )
    if existing:
        return {"message": "Already completed today", "streak": calculate_streak(habit)}
    db.add(models.Completion(habit_id=habit_id, date=today))
    db.commit()
    db.refresh(habit)
    return {"message": "Done!", "streak": calculate_streak(habit)}


def delete_habit_for_user(
    user: models.User, habit_id: int, db: Session
) -> dict:
    from fastapi import HTTPException

    habit = (
        db.query(models.Habit)
        .filter(models.Habit.id == habit_id, models.Habit.user_id == user.id)
        .first()
    )
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    habit.is_active = False
    db.commit()
    return {"message": "Deleted"}


def create_insight(
    user: models.User,
    insight_type: str,
    content: str,
    db: Session,
    *,
    habit_id: Optional[int] = None,
    context: Optional[str] = None,
) -> models.AIInsight:
    insight = models.AIInsight(
        user_id=user.id,
        insight_type=insight_type,
        content=content,
        habit_id=habit_id,
        context=context,
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return insight


def insight_to_out(ins: models.AIInsight, db: Session) -> AIInsightOut:
    habit_name = None
    if ins.habit_id:
        habit = db.query(models.Habit).filter(models.Habit.id == ins.habit_id).first()
        habit_name = habit.name if habit else None
    return AIInsightOut(
        id=ins.id,
        insight_type=ins.insight_type,
        content=ins.content,
        habit_id=ins.habit_id,
        habit_name=habit_name,
        context=ins.context,
        created_at=ins.created_at,
    )


def list_insights(user_id: int, db: Session) -> list[AIInsightOut]:
    insights = (
        db.query(models.AIInsight)
        .filter(models.AIInsight.user_id == user_id)
        .order_by(models.AIInsight.created_at.desc())
        .all()
    )
    return [insight_to_out(ins, db) for ins in insights]
