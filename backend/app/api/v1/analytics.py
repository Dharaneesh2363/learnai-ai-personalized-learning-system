from datetime import datetime, timedelta
from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_role
from app.models.assessment import Quiz, QuizAnswer, QuizAttempt
from app.models.course import Course, Topic
from app.models.mastery import LearningEvent, MasteryLevel, TopicMastery
from app.models.user import User, UserRole
from app.schemas.analytics import (
    ActivityItem,
    AdminAnalyticsResponse,
    DashboardAnalyticsResponse,
    QuizTrendItem,
    TopicScoreItem,
)

router = APIRouter(prefix="/analytics", tags=["Analytics & Telemetry"])


@router.get("/dashboard", response_model=DashboardAnalyticsResponse)
def get_student_dashboard_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Calculates student learning analytics, trends, streaks, and mastery telemetry."""
    # 1. Topic Masteries
    masteries = (
        db.query(TopicMastery)
        .filter(TopicMastery.user_id == current_user.id)
        .all()
    )

    total_mastery = sum(m.mastery_score for m in masteries)
    overall_mastery = round(total_mastery / len(masteries), 1) if masteries else 0.0

    mastered_count = sum(1 for m in masteries if m.level == MasteryLevel.MASTERED)
    in_progress_count = sum(1 for m in masteries if m.level in [MasteryLevel.DEVELOPING, MasteryLevel.PROFICIENT])

    mastery_by_topic = []
    weak_concepts_set = set()
    strong_concepts_set = set()

    m_topic_ids = [m.topic_id for m in masteries]
    topics_map = {t.id: t for t in db.query(Topic).filter(Topic.id.in_(m_topic_ids)).all()} if m_topic_ids else {}

    for m in masteries:
        topic = topics_map.get(m.topic_id)
        mastery_by_topic.append(
            TopicScoreItem(
                topic_id=m.topic_id,
                topic_title=topic.title if topic else "Topic",
                mastery_score=m.mastery_score,
                level=m.level.value,
                current_difficulty=m.current_difficulty.value
            )
        )
        if m.weak_concepts:
            for c in m.weak_concepts:
                weak_concepts_set.add(c)
        if m.strong_concepts:
            for c in m.strong_concepts:
                strong_concepts_set.add(c)

    # 2. Quiz Attempts & Trends
    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == current_user.id, QuizAttempt.is_completed == True)
        .order_by(QuizAttempt.started_at)
        .all()
    )

    quizzes_taken = len(attempts)
    avg_score = round(sum(a.percentage for a in attempts) / quizzes_taken, 1) if quizzes_taken else 0.0

    recent_attempts = attempts[-10:]
    recent_quiz_ids = [a.quiz_id for a in recent_attempts]
    quizzes_map = {q.id: q for q in db.query(Quiz).filter(Quiz.id.in_(recent_quiz_ids)).all()} if recent_quiz_ids else {}

    quiz_trends = []
    for a in recent_attempts:
        quiz = quizzes_map.get(a.quiz_id)
        quiz_trends.append(
            QuizTrendItem(
                attempt_id=a.id,
                quiz_title=quiz.title if quiz else "Quiz",
                percentage=a.percentage,
                date=a.started_at.strftime("%b %d")
            )
        )

    # 3. Learning streak calculation from learning_events
    events = (
        db.query(LearningEvent)
        .filter(LearningEvent.user_id == current_user.id)
        .order_by(LearningEvent.created_at.desc())
        .all()
    )

    # Calculate streak (consecutive days with at least 1 event)
    event_days = sorted({e.created_at.date() for e in events}, reverse=True)
    streak_days = 0
    today = datetime.utcnow().date()
    current_check = today

    for day in event_days:
        if day == current_check or day == (current_check - timedelta(days=1)):
            streak_days += 1
            current_check = day
        else:
            break
    
    if streak_days == 0 and event_days and event_days[0] == today:
        streak_days = 1

    # 4. Activity breakdown for past 7 days
    activity_items = []
    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        count = sum(1 for e in events if e.created_at.date() == target_date)
        activity_items.append(
            ActivityItem(
                date=target_date.strftime("%a"),
                event_count=count
            )
        )

    # 5. Time spent estimate
    total_time_spent = (quizzes_taken * 12) + (len(events) * 5)

    return DashboardAnalyticsResponse(
        overall_mastery=overall_mastery,
        quizzes_taken=quizzes_taken,
        average_quiz_score=avg_score,
        learning_streak_days=max(1, streak_days),
        total_time_spent_minutes=total_time_spent,
        topics_in_progress=in_progress_count,
        topics_mastered=mastered_count,
        mastery_by_topic=mastery_by_topic,
        quiz_trend=quiz_trends,
        recent_activity=activity_items,
        top_weak_concepts=list(weak_concepts_set)[:5],
        top_strong_concepts=list(strong_concepts_set)[:5]
    )


@router.get("/admin", response_model=AdminAnalyticsResponse)
def get_admin_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER))
) -> Any:
    """Platform-wide analytical metrics for educators and administrators."""
    total_students = db.query(User).filter(User.role == UserRole.STUDENT).count()
    total_courses = db.query(Course).count()
    total_quizzes_completed = db.query(QuizAttempt).filter(QuizAttempt.is_completed == True).count()

    all_mastery_scores = db.query(TopicMastery.mastery_score).all()
    avg_mastery = (
        round(sum(m[0] for m in all_mastery_scores) / len(all_mastery_scores), 1)
        if all_mastery_scores else 0.0
    )

    week_ago = datetime.utcnow() - timedelta(days=7)
    active_students = (
        db.query(LearningEvent.user_id)
        .filter(LearningEvent.created_at >= week_ago)
        .distinct()
        .count()
    )

    # Low performing topics
    topics = db.query(Topic).all()
    topic_performance = []
    for t in topics:
        t_masteries = db.query(TopicMastery).filter(TopicMastery.topic_id == t.id).all()
        if t_masteries:
            avg_t = sum(m.mastery_score for m in t_masteries) / len(t_masteries)
            topic_performance.append({
                "topic_id": t.id,
                "title": t.title,
                "average_mastery": round(avg_t, 1),
                "student_count": len(t_masteries)
            })

    low_performing = sorted(topic_performance, key=lambda x: x["average_mastery"])[:5]

    courses = db.query(Course).all()
    high_engagement = []
    for c in courses:
        high_engagement.append({
            "course_id": c.id,
            "title": c.title,
            "modules_count": len(c.modules),
            "quizzes_count": len(c.quizzes)
        })

    return AdminAnalyticsResponse(
        total_students=total_students,
        total_courses=total_courses,
        total_quizzes_completed=total_quizzes_completed,
        average_platform_mastery=avg_mastery,
        active_students_last_7_days=active_students,
        low_performing_topics=low_performing,
        high_engagement_courses=high_engagement
    )
