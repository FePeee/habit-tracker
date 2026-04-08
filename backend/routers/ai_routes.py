from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from ai import call_ai
from auth import get_current_user
from database import get_db
from schemas import (
    AIInsightOut,
    HabitAdviceRequest,
    RoleModelRequest,
    SuggestHabitsRequest,
    BotHabitAdviceRequest,
    BotRoleModelRequest,
    BotSuggestHabitsRequest,
)
from services import (
    calculate_streak,
    get_active_habits,
    get_user_by_telegram,
    create_insight,
    insight_to_out,
    list_insights,
)

router = APIRouter(prefix="/api", tags=["ai"])


def _build_advice_prompt(user_name: str, habit_name: str, issue: str, habit_context: str) -> str:
    return f"""You are a habit optimization coach. The user needs advice about their habit.

User: {user_name}
Habit: {habit_name}
Issue: {issue}{habit_context}

Provide:
1. One specific, actionable strategy to overcome this issue
2. A psychological insight about why this happens
3. A small experiment to try for the next 3 days

Be concise, friendly, and practical. Use emojis."""


def _build_rolemodel_prompt(role: str, existing: str) -> str:
    return f"""You are a career and habit coach. The user wants to develop habits like a specific type of person.

Target role/profession: {role}
Current habits: {existing}

Suggest 3-5 specific daily or weekly habits that would help them embody the best qualities of this role.
For each habit, explain:
1. What the habit is
2. Why it matters for this role
3. How to start small (first week)

Be inspiring but realistic. Use emojis."""


def _build_suggest_prompt(user_name: str, current_text: str, goal: str | None) -> str:
    goal_context = f"\nUser's goal: {goal}" if goal else ""
    return f"""You are a habit design expert. Help this user build better habits.

User: {user_name}
Current habits: {current_text}{goal_context}

Suggest 3-5 complementary habits that would work well together.
For each suggestion:
1. Name the habit clearly
2. Explain why it's valuable
3. Give a simple daily action (takes < 5 min to start)
4. Share one common pitfall to avoid

Be warm, practical, and motivating. Use emojis."""


def _get_habit_context(user: models.User, habit_name: str, db: Session) -> tuple[models.Habit | None, str]:
    habit = (
        db.query(models.Habit)
        .filter(
            models.Habit.user_id == user.id,
            models.Habit.name.ilike(habit_name),
            models.Habit.is_active == True,
        )
        .first()
    )
    context = ""
    if habit:
        streak = calculate_streak(habit)
        today = date.today()
        week_start = today - timedelta(days=6)
        week_done = sum(1 for c in habit.completions if week_start <= c.date <= today)
        done_today = any(c.date == today for c in habit.completions)
        context = f"\nHabit stats: streak={streak} days, this week={week_done}/7, done today={done_today}"
    return habit, context


async def _handle_advice(user: models.User, habit_name: str, issue: str, db: Session) -> AIInsightOut:
    habit, habit_context = _get_habit_context(user, habit_name, db)
    prompt = _build_advice_prompt(user.name, habit_name, issue, habit_context)
    content = await call_ai(prompt)
    insight = create_insight(
        user, "habit_advice", content, db,
        habit_id=habit.id if habit else None,
        context=f"Habit: {habit_name}, Issue: {issue}",
    )
    return AIInsightOut(
        id=insight.id, insight_type=insight.insight_type, content=insight.content,
        habit_id=insight.habit_id,
        habit_name=habit.name if habit else habit_name,
        context=insight.context, created_at=insight.created_at,
    )


async def _handle_rolemodel(user: models.User, role: str, existing_habits: list[str], db: Session) -> AIInsightOut:
    existing = ", ".join(existing_habits) if existing_habits else "none yet"
    prompt = _build_rolemodel_prompt(role, existing)
    content = await call_ai(prompt)
    insight = create_insight(
        user, "role_model", content, db, context=f"Role: {role}",
    )
    return insight_to_out(insight, db)


async def _handle_suggest(user: models.User, goal: str | None, db: Session) -> AIInsightOut:
    habits = get_active_habits(user.id, db)
    current_names = [h.name for h in habits]
    current_text = ", ".join(current_names) if current_names else "no habits yet"
    prompt = _build_suggest_prompt(user.name, current_text, goal)
    content = await call_ai(prompt)
    insight = create_insight(
        user, "suggest_habits", content, db, context=goal or "General suggestions",
    )
    return insight_to_out(insight, db)


# ---- JWT-authenticated endpoints ----

@router.post("/ai-habit-advice", response_model=AIInsightOut)
async def get_habit_advice(
    data: HabitAdviceRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await _handle_advice(current_user, data.habit_name, data.issue, db)


@router.post("/ai-role-model-habits", response_model=AIInsightOut)
async def get_role_model_habits(
    data: RoleModelRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await _handle_rolemodel(current_user, data.role_or_profession, data.existing_habits or [], db)


@router.post("/ai-suggest-habits", response_model=AIInsightOut)
async def suggest_habits(
    data: SuggestHabitsRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await _handle_suggest(current_user, data.goal, db)


@router.get("/ai-insights", response_model=List[AIInsightOut])
def get_ai_insights(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_insights(current_user.id, db)


@router.delete("/ai-insights/{insight_id}")
def delete_ai_insight(
    insight_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    insight = (
        db.query(models.AIInsight)
        .filter(models.AIInsight.id == insight_id, models.AIInsight.user_id == current_user.id)
        .first()
    )
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    db.delete(insight)
    db.commit()
    return {"message": "Deleted"}


# ---- Bot endpoints (auth by telegram_id) ----

@router.post("/bot/ai-habit-advice", response_model=AIInsightOut)
async def bot_get_habit_advice(data: BotHabitAdviceRequest, db: Session = Depends(get_db)):
    user = get_user_by_telegram(data.telegram_id, db)
    return await _handle_advice(user, data.habit_name, data.issue, db)


@router.post("/bot/ai-role-model-habits", response_model=AIInsightOut)
async def bot_get_role_model_habits(data: BotRoleModelRequest, db: Session = Depends(get_db)):
    user = get_user_by_telegram(data.telegram_id, db)
    return await _handle_rolemodel(user, data.role_or_profession, data.existing_habits or [], db)


@router.post("/bot/ai-suggest-habits", response_model=AIInsightOut)
async def bot_suggest_habits(data: BotSuggestHabitsRequest, db: Session = Depends(get_db)):
    user = get_user_by_telegram(data.telegram_id, db)
    return await _handle_suggest(user, data.goal, db)


@router.get("/bot/ai-insights/{telegram_id}", response_model=List[AIInsightOut])
def bot_get_ai_insights(telegram_id: str, db: Session = Depends(get_db)):
    user = get_user_by_telegram(telegram_id, db)
    return list_insights(user.id, db)
