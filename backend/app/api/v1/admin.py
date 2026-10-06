from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_role
from app.models.assessment import Question, QuestionDifficulty, QuestionType, Quiz, QuizQuestion
from app.models.course import Course, Lesson, Module, Topic
from app.models.mastery import TopicMastery
from app.models.user import User, UserRole
from app.schemas.assessment import QuestionCreate, QuestionFullResponse
from app.schemas.user import UserResponse
from app.services.ai.factory import get_ai_provider

router = APIRouter(prefix="/admin", tags=["Admin & Teacher Management"])


class GenerateQuestionsRequest(BaseModel):
    topic_id: int
    difficulty: str = "medium"
    count: int = 3
    weak_concepts: List[str] = []


@router.get("/students", response_model=List[Dict[str, Any]])
def list_students(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER))
) -> Any:
    """List all registered students with aggregate mastery and quiz counts."""
    students = db.query(User).filter(User.role == UserRole.STUDENT).all()
    results = []
    for s in students:
        masteries = db.query(TopicMastery).filter(TopicMastery.user_id == s.id).all()
        avg_score = round(sum(m.mastery_score for m in masteries) / len(masteries), 1) if masteries else 0.0
        results.append({
            "id": s.id,
            "email": s.email,
            "full_name": s.full_name,
            "is_active": s.is_active,
            "created_at": s.created_at,
            "topics_enrolled": len(masteries),
            "average_mastery": avg_score,
            "quizzes_attempted": len(s.quiz_attempts)
        })
    return results


@router.get("/questions", response_model=List[QuestionFullResponse])
def list_questions(
    topic_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER))
) -> Any:
    """List questions in question bank."""
    query = db.query(Question)
    if topic_id:
        query = query.filter(Question.topic_id == topic_id)
    return query.order_by(Question.id.desc()).all()


@router.post("/questions", response_model=QuestionFullResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    req: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER))
) -> Any:
    """Manually add question to question bank."""
    question = Question(**req.model_dump(), is_ai_generated=False)
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.delete("/questions/{question_id}")
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER))
) -> Any:
    """Delete a question."""
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(q)
    db.commit()
    return {"message": "Question deleted successfully"}


@router.post("/generate-ai-questions", response_model=List[QuestionFullResponse])
def generate_ai_questions_for_topic(
    req: GenerateQuestionsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER))
) -> Any:
    """
    Generate new curriculum-aligned questions using AI provider.
    Validates output structure and persists to question bank.
    """
    topic = db.query(Topic).filter(Topic.id == req.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    from app.services.content_retriever import LearningContextRetriever
    rag_context = LearningContextRetriever.retrieve_context_for_topic(
        db=db, topic_id=topic.id, max_lessons=2
    )

    ai_provider = get_ai_provider()
    raw_questions = ai_provider.generate_questions(
        topic_title=topic.title,
        difficulty=req.difficulty,
        weak_concepts=req.weak_concepts,
        count=req.count
    )

    created_questions = []
    for q_data in raw_questions:
        if not q_data.get("question_text"):
            continue

        # Safe difficulty normalization
        diff_str = str(q_data.get("difficulty", "medium")).lower().strip()
        if diff_str in ["easy", "beginner", "simple", "introductory"]:
            diff = QuestionDifficulty.EASY
        elif diff_str in ["hard", "advanced", "expert", "complex"]:
            diff = QuestionDifficulty.HARD
        else:
            diff = QuestionDifficulty.MEDIUM

        q_type = QuestionType.MULTIPLE_CHOICE
        options = q_data.get("options_json", [])
        if not isinstance(options, list) or len(options) < 2:
            options = [
                {"id": "A", "text": "Valid approach"},
                {"id": "B", "text": "Syntax error"},
                {"id": "C", "text": "Runtime exception"},
                {"id": "D", "text": "None of the above"}
            ]

        question = Question(
            topic_id=topic.id,
            question_text=q_data["question_text"],
            explanation=q_data.get("explanation", f"Pedagogical explanation for {topic.title}"),
            difficulty=diff,
            question_type=q_type,
            options_json=options,
            correct_answer=str(q_data.get("correct_answer", "A")).strip().upper(),
            concept_tag=q_data.get("concept_tag", topic.slug),
            points=int(q_data.get("points", 2)),
            is_ai_generated=True
        )
        db.add(question)
        created_questions.append(question)

    db.commit()
    for q in created_questions:
        db.refresh(q)

    return created_questions
