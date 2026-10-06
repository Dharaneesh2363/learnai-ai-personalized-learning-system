from app.core.database import Base
from app.models.user import User, UserRole
from app.models.course import (
    Course,
    CourseDifficulty,
    Module,
    Topic,
    TopicPrerequisite,
    Lesson,
    Resource,
    ResourceType,
)
from app.models.assessment import (
    Question,
    QuestionDifficulty,
    QuestionType,
    Quiz,
    QuizQuestion,
    QuizAttempt,
    QuizAnswer,
)
from app.models.mastery import (
    TopicMastery,
    MasteryTrend,
    MasteryLevel,
    LearningEvent,
    LearningEventType,
)
from app.models.recommendation import (
    Recommendation,
    RecommendationType,
    RecommendationPriority,
)
from app.models.study_plan import (
    StudyPlan,
    StudyPlanItem,
    PlanType,
)
from app.models.tutor import (
    ChatSession,
    ChatMessage,
    MessageRole,
)

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Course",
    "CourseDifficulty",
    "Module",
    "Topic",
    "TopicPrerequisite",
    "Lesson",
    "Resource",
    "ResourceType",
    "Question",
    "QuestionDifficulty",
    "QuestionType",
    "Quiz",
    "QuizQuestion",
    "QuizAttempt",
    "QuizAnswer",
    "TopicMastery",
    "MasteryTrend",
    "MasteryLevel",
    "LearningEvent",
    "LearningEventType",
    "Recommendation",
    "RecommendationType",
    "RecommendationPriority",
    "StudyPlan",
    "StudyPlanItem",
    "PlanType",
    "ChatSession",
    "ChatMessage",
    "MessageRole",
]
