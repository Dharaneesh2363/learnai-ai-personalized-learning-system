from datetime import datetime
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_role
from app.models.assessment import (
    Question,
    QuestionDifficulty,
    Quiz,
    QuizAnswer,
    QuizAttempt,
    QuizQuestion,
)
from app.models.course import Course, Topic
from app.models.mastery import TopicMastery, LearningEvent, LearningEventType
from app.models.user import User, UserRole
from app.schemas.assessment import (
    AdaptiveStepResponse,
    AnswerResultResponse,
    QuestionClientResponse,
    QuestionCreate,
    QuestionFullResponse,
    QuizAttemptDetailResponse,
    QuizAttemptResponse,
    QuizCreate,
    QuizSubmissionRequest,
    QuizSummaryResponse,
    QuizTakeResponse,
    SingleAnswerSubmitRequest,
)
from app.services.adaptive_quiz_service import AdaptiveQuizService
from app.services.mastery_service import MasteryEngine

router = APIRouter(prefix="/quizzes", tags=["Assessments & Adaptive Quizzes"])


@router.get("", response_model=List[QuizSummaryResponse])
def get_quizzes(
    course_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    db: Session = Depends(get_db)
) -> Any:
    """List available quizzes."""
    query = db.query(Quiz)
    if course_id:
        query = query.filter(Quiz.course_id == course_id)
    if topic_id:
        query = query.filter(Quiz.topic_id == topic_id)
    
    quizzes = query.all()
    results = []
    for q in quizzes:
        results.append(
            QuizSummaryResponse(
                id=q.id,
                course_id=q.course_id,
                topic_id=q.topic_id,
                title=q.title,
                description=q.description,
                time_limit_minutes=q.time_limit_minutes,
                passing_score=q.passing_score,
                is_adaptive=q.is_adaptive,
                created_at=q.created_at,
                question_count=len(q.quiz_questions) if not q.is_adaptive else 5
            )
        )
    return results


@router.get("/{quiz_id}/take", response_model=QuizTakeResponse)
def get_quiz_to_take(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve questions for taking the quiz.
    Never exposes correct answers or explanations to the client!
    """
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = []
    if quiz.is_adaptive:
        # Provide the initial adaptive question
        initial_diff = AdaptiveQuizService.get_initial_difficulty(db, current_user.id, quiz.topic_id)
        candidate = AdaptiveQuizService.select_next_question(
            db=db,
            quiz=quiz,
            target_difficulty=initial_diff,
            answered_question_ids=[],
            weak_concepts=[]
        )
        if candidate:
            questions.append(QuestionClientResponse.model_validate(candidate))
    else:
        # Standard quiz: list all associated questions in order
        quiz_questions = (
            db.query(QuizQuestion)
            .filter(QuizQuestion.quiz_id == quiz_id)
            .order_by(QuizQuestion.order_index)
            .all()
        )
        qq_ids = [qq.question_id for qq in quiz_questions]
        if qq_ids:
            questions_map = {q.id: q for q in db.query(Question).filter(Question.id.in_(qq_ids)).all()}
            for qq in quiz_questions:
                q = questions_map.get(qq.question_id)
                if q:
                    questions.append(QuestionClientResponse.model_validate(q))

    return QuizTakeResponse(
        id=quiz.id,
        course_id=quiz.course_id,
        topic_id=quiz.topic_id,
        title=quiz.title,
        description=quiz.description,
        time_limit_minutes=quiz.time_limit_minutes,
        passing_score=quiz.passing_score,
        is_adaptive=quiz.is_adaptive,
        questions=questions
    )


@router.post("/{quiz_id}/start-attempt", response_model=QuizAttemptResponse)
def start_quiz_attempt(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Start an active quiz attempt session."""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    attempt, _ = AdaptiveQuizService.start_quiz_attempt(
        db=db,
        user_id=current_user.id,
        quiz_id=quiz_id
    )
    return attempt


@router.post("/adaptive-step", response_model=AdaptiveStepResponse)
def submit_adaptive_step(
    req: SingleAnswerSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Submits a single answer in an adaptive quiz session.
    Dynamically recalculates difficulty, tracks mistakes, and yields next question.
    """
    try:
        step_result = AdaptiveQuizService.submit_step(
            db=db,
            user_id=current_user.id,
            attempt_id=req.attempt_id,
            question_id=req.question_id,
            selected_answer=req.selected_answer,
            time_spent_seconds=req.time_spent_seconds
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    next_q_resp = None
    if step_result["next_question"]:
        next_q_resp = QuestionClientResponse.model_validate(step_result["next_question"])

    return AdaptiveStepResponse(
        is_correct=step_result["is_correct"],
        explanation=step_result["explanation"],
        correct_answer=step_result["correct_answer"],
        current_difficulty=step_result["current_difficulty"],
        next_question=next_q_resp,
        is_completed=step_result["is_completed"],
        questions_answered=step_result["questions_answered"],
        total_questions=step_result["total_questions"]
    )


@router.post("/{quiz_id}/submit", response_model=QuizAttemptResponse)
def submit_standard_quiz(
    quiz_id: int,
    req: QuizSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Authoritative backend grading for batch-submitted standard quizzes.
    Validates answers, computes percentage, records answers, and triggers Mastery updates.
    """
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=current_user.id,
        score=0.0,
        max_score=0.0,
        percentage=0.0,
        passed=False,
        is_completed=False,
        current_difficulty=QuestionDifficulty.MEDIUM,
        started_at=datetime.utcnow()
    )
    db.add(attempt)
    db.flush()

    total_score = 0.0
    max_score = 0.0
    created_answers: List[QuizAnswer] = []

    sub_q_ids = [sub.question_id for sub in req.answers]
    q_map = {q.id: q for q in db.query(Question).filter(Question.id.in_(sub_q_ids)).all()} if sub_q_ids else {}

    for sub in req.answers:
        q = q_map.get(sub.question_id)
        if not q:
            continue

        is_corr = (sub.selected_answer.strip().upper() == q.correct_answer.strip().upper())
        pts = float(q.points) if is_corr else 0.0
        total_score += pts
        max_score += float(q.points)

        ans = QuizAnswer(
            attempt_id=attempt.id,
            question_id=q.id,
            selected_answer=sub.selected_answer,
            is_correct=is_corr,
            points_awarded=pts,
            time_spent_seconds=sub.time_spent_seconds,
            created_at=datetime.utcnow()
        )
        db.add(ans)
        created_answers.append(ans)

    pct = (total_score / max(1.0, max_score)) * 100.0
    attempt.score = round(total_score, 1)
    attempt.max_score = round(max_score, 1)
    attempt.percentage = round(pct, 1)
    attempt.passed = pct >= quiz.passing_score
    attempt.is_completed = True
    attempt.completed_at = datetime.utcnow()

    # Update Topic Mastery if associated with topic
    if quiz.topic_id and created_answers:
        MasteryEngine.update_topic_mastery_from_attempt(
            db=db,
            user_id=current_user.id,
            topic_id=quiz.topic_id,
            attempt=attempt,
            answers=created_answers
        )

    # Learning event
    event = LearningEvent(
        user_id=current_user.id,
        event_type=LearningEventType.QUIZ_COMPLETED,
        entity_type="quiz",
        entity_id=quiz.id,
        event_data={
            "attempt_id": attempt.id,
            "score": attempt.score,
            "percentage": attempt.percentage,
            "passed": attempt.passed,
        }
    )
    db.add(event)

    db.commit()
    db.refresh(attempt)
    return attempt


@router.get("/attempts/{attempt_id}", response_model=QuizAttemptDetailResponse)
def get_quiz_attempt_detail(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve comprehensive post-quiz report with question-level breakdown,
    correct answers, explanations, and mastery changes.
    """
    attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Quiz attempt not found")
    
    # Ownership verification (allow teachers/admins or student owner)
    if attempt.user_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot inspect another student's attempt")

    quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
    answers = (
        db.query(QuizAnswer)
        .filter(QuizAnswer.attempt_id == attempt.id)
        .all()
    )

    ans_q_ids = [a.question_id for a in answers]
    questions_map = {q.id: q for q in db.query(Question).filter(Question.id.in_(ans_q_ids)).all()} if ans_q_ids else {}

    answer_results = []
    for a in answers:
        q = questions_map.get(a.question_id)
        if q:
            answer_results.append(
                AnswerResultResponse(
                    question_id=q.id,
                    question_text=q.question_text,
                    selected_answer=a.selected_answer,
                    correct_answer=q.correct_answer,
                    is_correct=a.is_correct,
                    explanation=q.explanation,
                    points_awarded=a.points_awarded,
                    time_spent_seconds=a.time_spent_seconds
                )
            )

    # Find mastery change summary
    mastery_changes = []
    if quiz and quiz.topic_id:
        m = (
            db.query(TopicMastery)
            .filter(TopicMastery.user_id == attempt.user_id, TopicMastery.topic_id == quiz.topic_id)
            .first()
        )
        if m:
            mastery_changes.append({
                "topic_id": m.topic_id,
                "topic_title": m.topic.title if m.topic else "Topic",
                "mastery_score": m.mastery_score,
                "level": m.level.value,
                "trend": m.trend.value,
                "confidence": m.confidence
            })

    return QuizAttemptDetailResponse(
        id=attempt.id,
        quiz_id=attempt.quiz_id,
        user_id=attempt.user_id,
        quiz_title=quiz.title if quiz else "Quiz",
        score=attempt.score,
        max_score=attempt.max_score,
        percentage=attempt.percentage,
        passed=attempt.passed,
        is_completed=attempt.is_completed,
        current_difficulty=attempt.current_difficulty,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
        answers=answer_results,
        mastery_changes=mastery_changes
    )
