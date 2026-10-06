from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.models.assessment import QuestionDifficulty, QuestionType


class OptionItem(BaseModel):
    id: str
    text: str


class QuestionBase(BaseModel):
    topic_id: int
    question_text: str
    explanation: str
    difficulty: QuestionDifficulty = QuestionDifficulty.MEDIUM
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE
    options_json: List[Dict[str, Any]]
    correct_answer: str
    concept_tag: Optional[str] = None
    points: int = 1


class QuestionCreate(QuestionBase):
    pass


class QuestionClientResponse(BaseModel):
    """Safe response for student quiz taking - does NOT leak correct_answer or explanation."""
    id: int
    topic_id: int
    question_text: str
    difficulty: QuestionDifficulty
    question_type: QuestionType
    options_json: List[Dict[str, Any]]
    points: int
    concept_tag: Optional[str] = None

    class Config:
        from_attributes = True


class QuestionFullResponse(QuestionBase):
    """Admin / Post-assessment review view including explanations and correct answers."""
    id: int
    is_ai_generated: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuizBase(BaseModel):
    course_id: int
    topic_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    time_limit_minutes: int = 15
    passing_score: float = 70.0
    is_adaptive: bool = False


class QuizCreate(QuizBase):
    question_ids: Optional[List[int]] = None


class QuizSummaryResponse(QuizBase):
    id: int
    created_at: datetime
    question_count: int = 0

    class Config:
        from_attributes = True


class QuizTakeResponse(QuizBase):
    id: int
    questions: List[QuestionClientResponse] = []

    class Config:
        from_attributes = True


class AnswerSubmission(BaseModel):
    question_id: int
    selected_answer: str
    time_spent_seconds: int = 0


class QuizSubmissionRequest(BaseModel):
    answers: List[AnswerSubmission]


class SingleAnswerSubmitRequest(BaseModel):
    """Used for real-time adaptive quiz stepping."""
    attempt_id: int
    question_id: int
    selected_answer: str
    time_spent_seconds: int = 0


class AdaptiveStepResponse(BaseModel):
    is_correct: bool
    explanation: str
    correct_answer: str
    current_difficulty: QuestionDifficulty
    next_question: Optional[QuestionClientResponse] = None
    is_completed: bool
    questions_answered: int
    total_questions: int


class AnswerResultResponse(BaseModel):
    question_id: int
    question_text: str
    selected_answer: Optional[str]
    correct_answer: str
    is_correct: bool
    explanation: str
    points_awarded: float
    time_spent_seconds: int


class QuizAttemptResponse(BaseModel):
    id: int
    quiz_id: int
    user_id: int
    score: float
    max_score: float
    percentage: float
    passed: bool
    is_completed: bool
    current_difficulty: QuestionDifficulty
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QuizAttemptDetailResponse(QuizAttemptResponse):
    quiz_title: str
    answers: List[AnswerResultResponse] = []
    mastery_changes: List[Dict[str, Any]] = []
