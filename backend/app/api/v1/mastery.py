from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.models.course import Course, Module, Topic
from app.models.mastery import MasteryLevel, TopicMastery
from app.models.user import User
from app.schemas.mastery import MasterySummaryResponse, TopicMasteryResponse
from app.services.mastery_service import MasteryEngine

router = APIRouter(prefix="/mastery", tags=["Topic Mastery & Knowledge Tracing"])


@router.get("/summary", response_model=MasterySummaryResponse)
def get_mastery_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Retrieve summarized topic mastery metrics, weak spots, and strengths."""
    masteries = (
        db.query(TopicMastery)
        .filter(TopicMastery.user_id == current_user.id)
        .all()
    )

    # Apply Ebbinghaus decay if topics have been inactive for over a week
    for m in masteries:
        MasteryEngine.apply_decay_if_needed(db, m)

    all_topics = (
        db.query(Topic)
        .options(joinedload(Topic.module).joinedload(Module.course))
        .all()
    )
    topic_map = {t.id: t for t in all_topics}

    topic_responses = []
    total_score = 0.0
    mastered = 0
    proficient = 0
    developing = 0
    beginner = 0

    for m in masteries:
        topic = topic_map.get(m.topic_id)
        module = topic.module if topic else None
        course = module.course if module else None

        resp = TopicMasteryResponse(
            id=m.id,
            user_id=m.user_id,
            topic_id=m.topic_id,
            topic_title=topic.title if topic else "Topic",
            module_title=module.title if module else "Module",
            course_title=course.title if course else "Course",
            course_id=course.id if course else None,
            mastery_score=m.mastery_score,
            confidence=m.confidence,
            attempts_count=m.attempts_count,
            correct_answers=m.correct_answers,
            incorrect_answers=m.incorrect_answers,
            last_practiced_at=m.last_practiced_at,
            trend=m.trend,
            current_difficulty=m.current_difficulty,
            weak_concepts=m.weak_concepts or [],
            strong_concepts=m.strong_concepts or [],
            level=m.level,
            updated_at=m.updated_at
        )
        topic_responses.append(resp)
        total_score += m.mastery_score

        if m.level == MasteryLevel.MASTERED:
            mastered += 1
        elif m.level == MasteryLevel.PROFICIENT:
            proficient += 1
        elif m.level == MasteryLevel.DEVELOPING:
            developing += 1
        else:
            beginner += 1

    overall_mastery = round(total_score / len(masteries), 1) if masteries else 0.0

    # Sort topics
    sorted_by_score = sorted(topic_responses, key=lambda x: x.mastery_score)
    top_weak = sorted_by_score[:3] if sorted_by_score else []
    top_strong = sorted(topic_responses, key=lambda x: x.mastery_score, reverse=True)[:3] if sorted_by_score else []

    return MasterySummaryResponse(
        overall_mastery=overall_mastery,
        total_topics=len(masteries),
        mastered_count=mastered,
        proficient_count=proficient,
        developing_count=developing,
        beginner_count=beginner,
        top_weak_topics=top_weak,
        top_strong_topics=top_strong,
        topics=topic_responses
    )


@router.get("/topics", response_model=List[TopicMasteryResponse])
def get_user_topic_masteries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List student's topic mastery records without N+1 query overhead."""
    masteries = (
        db.query(TopicMastery)
        .filter(TopicMastery.user_id == current_user.id)
        .all()
    )

    for m in masteries:
        MasteryEngine.apply_decay_if_needed(db, m)

    all_topics = (
        db.query(Topic)
        .options(joinedload(Topic.module).joinedload(Module.course))
        .all()
    )
    topic_map = {t.id: t for t in all_topics}

    results = []
    for m in masteries:
        topic = topic_map.get(m.topic_id)
        module = topic.module if topic else None
        course = module.course if module else None

        results.append(
            TopicMasteryResponse(
                id=m.id,
                user_id=m.user_id,
                topic_id=m.topic_id,
                topic_title=topic.title if topic else "Topic",
                module_title=module.title if module else "Module",
                course_title=course.title if course else "Course",
                course_id=course.id if course else None,
                mastery_score=m.mastery_score,
                confidence=m.confidence,
                attempts_count=m.attempts_count,
                correct_answers=m.correct_answers,
                incorrect_answers=m.incorrect_answers,
                last_practiced_at=m.last_practiced_at,
                trend=m.trend,
                current_difficulty=m.current_difficulty,
                weak_concepts=m.weak_concepts or [],
                strong_concepts=m.strong_concepts or [],
                level=m.level,
                updated_at=m.updated_at
            )
        )
    return results
