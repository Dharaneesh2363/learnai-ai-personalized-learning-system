from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.recommendation import RecommendationType, RecommendationPriority
from app.models.assessment import QuestionDifficulty


class RecommendationResponse(BaseModel):
    id: int
    user_id: int
    topic_id: Optional[int] = None
    lesson_id: Optional[int] = None
    topic_title: Optional[str] = None
    course_id: Optional[int] = None
    course_title: Optional[str] = None
    title: str
    what_description: str
    why_description: str
    evidence_description: str
    action_description: str
    priority: RecommendationPriority
    recommendation_type: RecommendationType
    difficulty: QuestionDifficulty
    estimated_duration_minutes: int
    is_completed: bool
    is_dismissed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecommendationFeedback(BaseModel):
    is_completed: Optional[bool] = None
    is_dismissed: Optional[bool] = None
