from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    telegram_id = Column(String, unique=True, nullable=True)
    link_code = Column(String, unique=True, nullable=True)
    timezone = Column(String, default="UTC")
    report_day = Column(String, nullable=True)  # "monday", "sunday", etc.
    report_time = Column(String, nullable=True)  # "18:00"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    habits = relationship("Habit", back_populates="owner", cascade="all, delete")

class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    reminder_time = Column(String, nullable=True)  # "08:00"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="habits")
    completions = relationship("Completion", back_populates="habit", cascade="all, delete")


class Completion(Base):
    __tablename__ = "completions"

    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    habit = relationship("Habit", back_populates="completions")


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    insight_type = Column(String, nullable=False)  # "habit_advice", "role_model", "suggest_habits", "weekly_report"
    content = Column(String, nullable=False)  # AI-generated text
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=True)  # Optional: linked habit
    context = Column(String, nullable=True)  # User-provided context (e.g., profession name)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User")
    habit = relationship("Habit")
