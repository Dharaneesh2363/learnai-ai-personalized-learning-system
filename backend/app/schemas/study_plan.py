from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.models.study_plan import PlanType


class StudyPlanItemBase(BaseModel):
    topic_id: Optional[int] = None
    lesson_id: Optional[int] = None
    day_of_week: int  # 0: Monday, 6: Sunday
    title: str
    description: Optional[str] = None
    estimated_minutes: int = 30


class StudyPlanItemCreate(StudyPlanItemBase):
    pass


class StudyPlanItemResponse(StudyPlanItemBase):
    id: int
    study_plan_id: int
    topic_title: Optional[str] = None
    course_title: Optional[str] = None
    is_completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class StudyPlanBase(BaseModel):
    title: str
    plan_type: PlanType = PlanType.WEEKLY
    start_date: datetime
    end_date: datetime
    target_hours: float = 5.0


class StudyPlanCreate(StudyPlanBase):
    pass


class StudyPlanResponse(StudyPlanBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    items: List[StudyPlanItemResponse] = []

    class Config:
        from_attributes = True
