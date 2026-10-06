from datetime import datetime, timedelta
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.course import Course, Lesson, Module, Topic
from app.models.mastery import LearningEvent, LearningEventType, TopicMastery
from app.models.recommendation import Recommendation
from app.models.study_plan import PlanType, StudyPlan, StudyPlanItem
from app.models.user import User
from app.schemas.study_plan import StudyPlanItemResponse, StudyPlanResponse
from app.services.recommendation_service import RecommendationEngine

router = APIRouter(prefix="/study-plans", tags=["Personalized Study Plans"])


@router.get("/current", response_model=StudyPlanResponse)
def get_current_study_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Retrieve current active weekly study plan, auto-generating if not created."""
    plan = (
        db.query(StudyPlan)
        .filter(StudyPlan.user_id == current_user.id, StudyPlan.is_active == True)
        .order_by(StudyPlan.created_at.desc())
        .first()
    )

    if not plan:
        plan = generate_study_plan_internal(db, current_user.id)

    # Format items without N+1 queries
    it_topic_ids = [it.topic_id for it in plan.items if it.topic_id]
    topics_map = {}
    if it_topic_ids:
        from sqlalchemy.orm import joinedload
        topics = (
            db.query(Topic)
            .options(joinedload(Topic.module).joinedload(Module.course))
            .filter(Topic.id.in_(it_topic_ids))
            .all()
        )
        topics_map = {t.id: t for t in topics}

    item_resps = []
    for it in plan.items:
        topic = topics_map.get(it.topic_id)
        module = topic.module if topic else None
        course = module.course if module else None

        item_resps.append(
            StudyPlanItemResponse(
                id=it.id,
                study_plan_id=it.study_plan_id,
                topic_id=it.topic_id,
                lesson_id=it.lesson_id,
                topic_title=topic.title if topic else None,
                course_title=course.title if course else None,
                day_of_week=it.day_of_week,
                title=it.title,
                description=it.description,
                estimated_minutes=it.estimated_minutes,
                is_completed=it.is_completed,
                completed_at=it.completed_at,
                created_at=it.created_at
            )
        )

    return StudyPlanResponse(
        id=plan.id,
        user_id=plan.user_id,
        title=plan.title,
        plan_type=plan.plan_type,
        start_date=plan.start_date,
        end_date=plan.end_date,
        target_hours=plan.target_hours,
        is_active=plan.is_active,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        items=item_resps
    )


@router.post("/items/{item_id}/toggle", response_model=StudyPlanItemResponse)
def toggle_study_plan_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Toggle completion status of a study plan action item."""
    item = db.query(StudyPlanItem).filter(StudyPlanItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Study plan item not found")

    plan = db.query(StudyPlan).filter(StudyPlan.id == item.study_plan_id).first()
    if not plan or plan.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    item.is_completed = not item.is_completed
    item.completed_at = datetime.utcnow() if item.is_completed else None

    # Check if all items in plan completed
    all_completed = all(i.is_completed for i in plan.items)
    if all_completed and item.is_completed:
        event = LearningEvent(
            user_id=current_user.id,
            event_type=LearningEventType.STUDY_PLAN_COMPLETED,
            entity_type="study_plan",
            entity_id=plan.id,
            event_data={"plan_title": plan.title}
        )
        db.add(event)

    db.commit()
    db.refresh(item)

    topic = db.query(Topic).filter(Topic.id == item.topic_id).first() if item.topic_id else None
    course = topic.module.course if (topic and topic.module) else None

    return StudyPlanItemResponse(
        id=item.id,
        study_plan_id=item.study_plan_id,
        topic_id=item.topic_id,
        lesson_id=item.lesson_id,
        topic_title=topic.title if topic else None,
        course_title=course.title if course else None,
        day_of_week=item.day_of_week,
        title=item.title,
        description=item.description,
        estimated_minutes=item.estimated_minutes,
        is_completed=item.is_completed,
        completed_at=item.completed_at,
        created_at=item.created_at
    )


@router.post("/generate", response_model=StudyPlanResponse)
def regenerate_study_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Explicitly regenerate study plan based on latest recommendations."""
    # Deactivate current plans
    db.query(StudyPlan).filter(
        StudyPlan.user_id == current_user.id,
        StudyPlan.is_active == True
    ).update({"is_active": False})
    db.commit()

    plan = generate_study_plan_internal(db, current_user.id)
    return get_current_study_plan(db=db, current_user=current_user)


def generate_study_plan_internal(db: Session, user_id: int) -> StudyPlan:
    """Internal helper to construct an adaptive weekly study plan."""
    start = datetime.utcnow()
    end = start + timedelta(days=7)

    plan = StudyPlan(
        user_id=user_id,
        title="Personalized Weekly Mastery Roadmap",
        plan_type=PlanType.WEEKLY,
        start_date=start,
        end_date=end,
        target_hours=4.5,
        is_active=True
    )
    db.add(plan)
    db.flush()

    # Retrieve recommendations or masteries
    recs = RecommendationEngine.generate_recommendations_for_user(db, user_id)
    topics = db.query(Topic).all()

    # Plan schedule across Monday to Friday / Weekend
    schedule_titles = [
        ("Monday", "Remediate Weak Concept"),
        ("Tuesday", "Core Lesson Theory"),
        ("Wednesday", "Hands-on Code Practice"),
        ("Thursday", "Adaptive Practice Quiz"),
        ("Friday", "Comprehensive Topic Review"),
    ]

    for day_idx, (day_name, default_title) in enumerate(schedule_titles):
        rec = recs[day_idx % len(recs)] if recs else None
        item_title = f"{day_name}: {rec.title if rec else default_title}"
        item_desc = rec.action_description if rec else f"Study session for {day_name}"
        topic_id = rec.topic_id if rec else (topics[0].id if topics else None)
        lesson_id = rec.lesson_id if rec else None

        item = StudyPlanItem(
            study_plan_id=plan.id,
            topic_id=topic_id,
            lesson_id=lesson_id,
            day_of_week=day_idx,
            title=item_title,
            description=item_desc,
            estimated_minutes=30,
            is_completed=False
        )
        db.add(item)

    db.commit()
    db.refresh(plan)
    return plan
