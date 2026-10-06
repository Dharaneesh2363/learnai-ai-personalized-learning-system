from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.models.mastery import MasteryTrend, MasteryLevel, LearningEventType
from app.models.assessment import QuestionDifficulty


class TopicMasteryResponse(BaseModel):
    id: int
    user_id: int
    topic_id: int
    topic_title: Optional[str] = None
    module_title: Optional[str] = None
    course_title: Optional[str] = None
    course_id: Optional[int] = None
    mastery_score: float
    confidence: float
    attempts_count: int
    correct_answers: int
    incorrect_answers: int
    last_practiced_at: datetime
    trend: MasteryTrend
    current_difficulty: QuestionDifficulty
    weak_concepts: List[str] = []
    strong_concepts: List[str] = []
    level: MasteryLevel
    updated_at: datetime

    class Config:
        from_attributes = True


class MasterySummaryResponse(BaseModel):
    overall_mastery: float
    total_topics: int
    mastered_count: int
    proficient_count: int
    developing_count: int
    beginner_count: int
    top_weak_topics: List[TopicMasteryResponse] = []
    top_strong_topics: List[TopicMasteryResponse] = []
    topics: List[TopicMasteryResponse] = []


class LearningEventCreate(BaseModel):
    event_type: LearningEventType
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    event_data: Optional[Dict[str, Any]] = None


class LearningEventResponse(BaseModel):
    id: int
    user_id: int
    event_type: LearningEventType
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    event_data: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True
