from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.course import Course, Lesson, Module, Topic
from app.models.mastery import LearningEvent, LearningEventType
from app.models.recommendation import Recommendation
from app.models.user import User
from app.schemas.recommendation import RecommendationFeedback, RecommendationResponse
from app.services.recommendation_service import RecommendationEngine

router = APIRouter(prefix="/recommendations", tags=["Personalized Recommendations"])


@router.get("", response_model=List[RecommendationResponse])
def get_recommendations(
    refresh: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve personalized, explainable learning recommendations.
    If refresh=true or none exist, evaluates current mastery profile and regenerates them.
    """
    existing = (
        db.query(Recommendation)
        .filter(
            Recommendation.user_id == current_user.id,
            Recommendation.is_completed == False,
            Recommendation.is_dismissed == False
        )
        .order_by(Recommendation.priority)
        .all()
    )

    if not existing or refresh:
        existing = RecommendationEngine.generate_recommendations_for_user(db, current_user.id)

    topic_ids = [r.topic_id for r in existing if r.topic_id]
    topics_map = {}
    if topic_ids:
        from sqlalchemy.orm import joinedload
        topics = (
            db.query(Topic)
            .options(joinedload(Topic.module).joinedload(Module.course))
            .filter(Topic.id.in_(topic_ids))
            .all()
        )
        topics_map = {t.id: t for t in topics}

    results = []
    for r in existing:
        topic = topics_map.get(r.topic_id)
        module = topic.module if topic else None
        course = module.course if module else None

        results.append(
            RecommendationResponse(
                id=r.id,
                user_id=r.user_id,
                topic_id=r.topic_id,
                lesson_id=r.lesson_id,
                topic_title=topic.title if topic else None,
                course_id=course.id if course else None,
                course_title=course.title if course else None,
                title=r.title,
                what_description=r.what_description,
                why_description=r.why_description,
                evidence_description=r.evidence_description,
                action_description=r.action_description,
                priority=r.priority,
                recommendation_type=r.recommendation_type,
                difficulty=r.difficulty,
                estimated_duration_minutes=r.estimated_duration_minutes,
                is_completed=r.is_completed,
                is_dismissed=r.is_dismissed,
                created_at=r.created_at,
                updated_at=r.updated_at
            )
        )
    return results


@router.get("/hero", response_model=Optional[RecommendationResponse])
def get_hero_recommendation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Retrieve top-priority recommendation for student dashboard hero card."""
    recs = get_recommendations(refresh=False, db=db, current_user=current_user)
    return recs[0] if recs else None


@router.post("/{rec_id}/action", response_model=RecommendationResponse)
def act_on_recommendation(
    rec_id: int,
    feedback: RecommendationFeedback,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Record student interaction with a recommendation (complete / dismiss)."""
    rec = (
        db.query(Recommendation)
        .filter(Recommendation.id == rec_id, Recommendation.user_id == current_user.id)
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    if feedback.is_completed is not None:
        rec.is_completed = feedback.is_completed
    if feedback.is_dismissed is not None:
        rec.is_dismissed = feedback.is_dismissed

    # Record learning event
    event = LearningEvent(
        user_id=current_user.id,
        event_type=LearningEventType.RECOMMENDATION_CLICKED,
        entity_type="recommendation",
        entity_id=rec.id,
        event_data={
            "action": "completed" if rec.is_completed else "dismissed" if rec.is_dismissed else "clicked",
            "type": rec.recommendation_type.value,
            "topic_id": rec.topic_id
        }
    )
    db.add(event)
    db.commit()
    db.refresh(rec)

    topic = db.query(Topic).filter(Topic.id == rec.topic_id).first() if rec.topic_id else None
    module = topic.module if topic else None
    course = module.course if module else None

    return RecommendationResponse(
        id=rec.id,
        user_id=rec.user_id,
        topic_id=rec.topic_id,
        lesson_id=rec.lesson_id,
        topic_title=topic.title if topic else None,
        course_id=course.id if course else None,
        course_title=course.title if course else None,
        title=rec.title,
        what_description=rec.what_description,
        why_description=rec.why_description,
        evidence_description=rec.evidence_description,
        action_description=rec.action_description,
        priority=rec.priority,
        recommendation_type=rec.recommendation_type,
        difficulty=rec.difficulty,
        estimated_duration_minutes=rec.estimated_duration_minutes,
        is_completed=rec.is_completed,
        is_dismissed=rec.is_dismissed,
        created_at=rec.created_at,
        updated_at=rec.updated_at
    )
