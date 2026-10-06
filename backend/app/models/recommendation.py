import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.assessment import QuestionDifficulty


class RecommendationType(str, enum.Enum):
    REVISION = "revision"
    PRACTICE_QUIZ = "practice_quiz"
    NEXT_TOPIC = "next_topic"
    CHALLENGE = "challenge"


class RecommendationPriority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)
    
    title = Column(String(255), nullable=False)
    # Explainability 4-factor framework
    what_description = Column(Text, nullable=False)
    why_description = Column(Text, nullable=False)
    evidence_description = Column(Text, nullable=False)
    action_description = Column(Text, nullable=False)
    
    priority = Column(Enum(RecommendationPriority), default=RecommendationPriority.MEDIUM, nullable=False)
    recommendation_type = Column(Enum(RecommendationType), default=RecommendationType.PRACTICE_QUIZ, nullable=False)
    difficulty = Column(Enum(QuestionDifficulty), default=QuestionDifficulty.MEDIUM, nullable=False)
    estimated_duration_minutes = Column(Integer, default=20, nullable=False)
    
    is_completed = Column(Boolean, default=False, nullable=False)
    is_dismissed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="recommendations")
    topic = relationship("Topic", back_populates="recommendations")
    lesson = relationship("Lesson")
