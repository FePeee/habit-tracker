from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
from auth import get_current_user
from database import get_db
from schemas import HabitCreate, HabitOut
from services import (
    get_active_habits,
    habit_to_out,
    complete_habit_for_user,
    delete_habit_for_user,
    normalize_reminder_time,
)

router = APIRouter(prefix="/api", tags=["habits"])


@router.get("/habits", response_model=List[HabitOut])
def get_habits(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    habits = get_active_habits(current_user.id, db)
    return [habit_to_out(h) for h in habits]


@router.post("/habits", response_model=HabitOut)
def create_habit(
    data: HabitCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    habit = models.Habit(
        user_id=current_user.id,
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


@router.delete("/habits/{habit_id}")
def delete_habit(
    habit_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return delete_habit_for_user(current_user, habit_id, db)


@router.post("/habits/{habit_id}/complete")
def complete_habit(
    habit_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return complete_habit_for_user(current_user, habit_id, db)
