from typing import Any, Dict, List
from pydantic import BaseModel


class TopicScoreItem(BaseModel):
    topic_id: int
    topic_title: str
    mastery_score: float
    level: str
    current_difficulty: str


class QuizTrendItem(BaseModel):
    attempt_id: int
    quiz_title: str
    percentage: float
    date: str


class ActivityItem(BaseModel):
    date: str
    event_count: int


class DashboardAnalyticsResponse(BaseModel):
    overall_mastery: float
    quizzes_taken: int
    average_quiz_score: float
    learning_streak_days: int
    total_time_spent_minutes: int
    topics_in_progress: int
    topics_mastered: int
    mastery_by_topic: List[TopicScoreItem] = []
    quiz_trend: List[QuizTrendItem] = []
    recent_activity: List[ActivityItem] = []
    top_weak_concepts: List[str] = []
    top_strong_concepts: List[str] = []


class AdminAnalyticsResponse(BaseModel):
    total_students: int
    total_courses: int
    total_quizzes_completed: int
    average_platform_mastery: float
    active_students_last_7_days: int
    low_performing_topics: List[Dict[str, Any]] = []
    high_engagement_courses: List[Dict[str, Any]] = []
