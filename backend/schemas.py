from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    telegram_id: Optional[str] = None
    link_code: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


class HabitCreate(BaseModel):
    name: str
    reminder_time: Optional[str] = None


class HabitOut(BaseModel):
    id: int
    name: str
    reminder_time: Optional[str] = None
    is_active: bool
    streak: int = 0
    done_today: bool = False

    class Config:
        from_attributes = True


class LinkTelegram(BaseModel):
    code: str
    telegram_id: str


class AIInsightOut(BaseModel):
    id: int
    insight_type: str
    content: str
    habit_id: Optional[int] = None
    habit_name: Optional[str] = None
    context: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HabitAdviceRequest(BaseModel):
    habit_name: str
    issue: str


class RoleModelRequest(BaseModel):
    role_or_profession: str
    existing_habits: Optional[List[str]] = []


class SuggestHabitsRequest(BaseModel):
    goal: Optional[str] = None


class BotHabitAdviceRequest(BaseModel):
    telegram_id: str
    habit_name: str
    issue: str


class BotRoleModelRequest(BaseModel):
    telegram_id: str
    role_or_profession: str
    existing_habits: Optional[List[str]] = []


class BotSuggestHabitsRequest(BaseModel):
    telegram_id: str
    goal: Optional[str] = None
