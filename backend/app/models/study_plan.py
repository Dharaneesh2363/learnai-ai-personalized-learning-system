import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from app.core.database import Base


class PlanType(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"


class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    plan_type = Column(Enum(PlanType), default=PlanType.WEEKLY, nullable=False)
    start_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_date = Column(DateTime, nullable=False)
    target_hours = Column(Float, default=5.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="study_plans")
    items = relationship("StudyPlanItem", back_populates="study_plan", cascade="all, delete-orphan", order_by="StudyPlanItem.day_of_week")


class StudyPlanItem(Base):
    __tablename__ = "study_plan_items"

    id = Column(Integer, primary_key=True, index=True)
    study_plan_id = Column(Integer, ForeignKey("study_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)
    day_of_week = Column(Integer, default=0, nullable=False)  # 0: Monday, ..., 6: Sunday
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    estimated_minutes = Column(Integer, default=30, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    study_plan = relationship("StudyPlan", back_populates="items")
    topic = relationship("Topic")
    lesson = relationship("Lesson")
