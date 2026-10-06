import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Float, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.assessment import QuestionDifficulty


class MasteryTrend(str, enum.Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


class MasteryLevel(str, enum.Enum):
    BEGINNER = "beginner"       # 0 - 39
    DEVELOPING = "developing"   # 40 - 59
    PROFICIENT = "proficient"   # 60 - 79
    MASTERED = "mastered"       # 80 - 100


class LearningEventType(str, enum.Enum):
    LESSON_STARTED = "lesson_started"
    LESSON_COMPLETED = "lesson_completed"
    QUIZ_STARTED = "quiz_started"
    QUESTION_ANSWERED = "question_answered"
    QUIZ_COMPLETED = "quiz_completed"
    TOPIC_PRACTICED = "topic_practiced"
    AI_QUESTION_ASKED = "ai_question_asked"
    RECOMMENDATION_CLICKED = "recommendation_clicked"
    STUDY_PLAN_COMPLETED = "study_plan_completed"


class TopicMastery(Base):
    __tablename__ = "topic_mastery"
    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uq_user_topic_mastery"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    
    mastery_score = Column(Float, default=0.0, nullable=False)  # 0.0 to 100.0
    confidence = Column(Float, default=0.0, nullable=False)     # 0.0 to 1.0
    attempts_count = Column(Integer, default=0, nullable=False)
    correct_answers = Column(Integer, default=0, nullable=False)
    incorrect_answers = Column(Integer, default=0, nullable=False)
    last_practiced_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    trend = Column(Enum(MasteryTrend), default=MasteryTrend.STABLE, nullable=False)
    current_difficulty = Column(Enum(QuestionDifficulty), default=QuestionDifficulty.EASY, nullable=False)
    weak_concepts = Column(JSON, default=list, nullable=False)
    strong_concepts = Column(JSON, default=list, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="topic_masteries")
    topic = relationship("Topic", back_populates="masteries")

    @property
    def level(self) -> MasteryLevel:
        if self.mastery_score >= 80:
            return MasteryLevel.MASTERED
        elif self.mastery_score >= 60:
            return MasteryLevel.PROFICIENT
        elif self.mastery_score >= 40:
            return MasteryLevel.DEVELOPING
        return MasteryLevel.BEGINNER


class LearningEvent(Base):
    __tablename__ = "learning_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(Enum(LearningEventType), nullable=False, index=True)
    entity_type = Column(String(100), nullable=True)  # e.g., "topic", "lesson", "quiz"
    entity_id = Column(Integer, nullable=True)
    event_data = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="learning_events")
