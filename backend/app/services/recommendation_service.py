import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from sqlalchemy.orm import Session

from app.models.assessment import QuestionDifficulty, Quiz, QuizAttempt
from app.models.course import Course, Lesson, Module, Topic, TopicPrerequisite
from app.models.mastery import MasteryLevel, MasteryTrend, TopicMastery
from app.models.recommendation import Recommendation, RecommendationPriority, RecommendationType
from app.services.mastery_service import MasteryEngine

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Dedicated Explainable Recommendation Engine.
    Employs the 4-factor framework: WHAT, WHY, EVIDENCE, ACTION.
    Includes prerequisite DAG cycle safeguards and bulk database lookups.
    """

    @classmethod
    def _detect_and_prune_cycles(cls, prereqs_map: Dict[int, List[int]]) -> Dict[int, List[int]]:
        """
        Detects circular dependencies in the topic prerequisite graph using DFS.
        Prunes back-edges that create cycles to prevent deadlock in learning paths.
        """
        safe_prereqs: Dict[int, List[int]] = defaultdict(list)
        visited: Set[int] = set()
        rec_stack: Set[int] = set()

        def dfs(node: int, path: List[int]) -> None:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in prereqs_map.get(node, []):
                if neighbor in rec_stack:
                    logger.warning(
                        f"Detected prerequisite cycle between Topic {node} and Topic {neighbor}. "
                        f"Pruning edge {neighbor} -> {node}."
                    )
                    continue  # Break cycle
                safe_prereqs[node].append(neighbor)
                if neighbor not in visited:
                    dfs(neighbor, path + [neighbor])

            rec_stack.remove(node)

        for topic_id in list(prereqs_map.keys()):
            if topic_id not in visited:
                dfs(topic_id, [topic_id])

        return safe_prereqs

    @classmethod
    def generate_recommendations_for_user(cls, db: Session, user_id: int) -> List[Recommendation]:
        """
        Synthesizes student's mastery profile, mistake history, and prerequisite graph
        to generate personalized, explainable recommendations without N+1 query overhead.
        """
        masteries = (
            db.query(TopicMastery)
            .filter(TopicMastery.user_id == user_id)
            .all()
        )

        # Apply forgetting curve decay to ensure freshest mastery perspective
        for m in masteries:
            MasteryEngine.apply_decay_if_needed(db, m)

        all_topics = db.query(Topic).order_by(Topic.order_index).all()
        topic_map = {t.id: t for t in all_topics}

        # Bulk pre-load published lessons grouped by topic_id to avoid inner-loop queries
        all_lessons = (
            db.query(Lesson)
            .filter(Lesson.is_published == True)
            .order_by(Lesson.order_index)
            .all()
        )
        first_lesson_by_topic: Dict[int, Lesson] = {}
        last_lesson_by_topic: Dict[int, Lesson] = {}
        for l in all_lessons:
            if l.topic_id not in first_lesson_by_topic:
                first_lesson_by_topic[l.topic_id] = l
            last_lesson_by_topic[l.topic_id] = l

        # Bulk pre-load all topic prerequisites
        raw_prereqs = db.query(TopicPrerequisite).all()
        prereqs_by_topic: Dict[int, List[int]] = defaultdict(list)
        for p in raw_prereqs:
            prereqs_by_topic[p.topic_id].append(p.prerequisite_topic_id)

        safe_prereqs = cls._detect_and_prune_cycles(prereqs_by_topic)

        # Clear old non-completed recommendations for this user
        db.query(Recommendation).filter(
            Recommendation.user_id == user_id,
            Recommendation.is_completed == False
        ).delete()
        db.flush()

        recommendations: List[Recommendation] = []

        # 1. Identify critical weak areas (Mastery < 50% with attempts)
        weak_masteries = [m for m in masteries if m.mastery_score < 50.0 and m.attempts_count > 0]
        weak_masteries.sort(key=lambda m: m.mastery_score)

        for wm in weak_masteries[:2]:
            topic = topic_map.get(wm.topic_id)
            if not topic:
                continue

            lesson = first_lesson_by_topic.get(topic.id)
            weak_concepts_str = ", ".join(wm.weak_concepts) if wm.weak_concepts else "core fundamentals"
            
            rec = Recommendation(
                user_id=user_id,
                topic_id=topic.id,
                lesson_id=lesson.id if lesson else None,
                title=f"Targeted Remediation: {topic.title}",
                what_description=f"Prioritize practicing '{topic.title}' to build solid foundational competence.",
                why_description=(
                    f"Your mastery is currently {wm.mastery_score}% (Beginner/Developing level) with a "
                    f"{wm.trend.value} trend. Targeted focus here will prevent stumbling on advanced concepts."
                ),
                evidence_description=(
                    f"You have answered {wm.correct_answers} of {wm.correct_answers + wm.incorrect_answers} questions correctly "
                    f"({round(wm.correct_answers / max(1, wm.correct_answers + wm.incorrect_answers) * 100, 1)}% accuracy), "
                    f"with persistent mistakes in: {weak_concepts_str}."
                ),
                action_description=(
                    f"Review the lesson '{lesson.title if lesson else topic.title}' and take a 5-question adaptive quiz at "
                    f"easy-to-medium difficulty."
                ),
                priority=RecommendationPriority.HIGH,
                recommendation_type=RecommendationType.REVISION,
                difficulty=QuestionDifficulty.EASY if wm.mastery_score < 35 else QuestionDifficulty.MEDIUM,
                estimated_duration_minutes=25,
            )
            recommendations.append(rec)

        # 2. Identify developing topics (50% <= Mastery < 75%) needing reinforcement
        developing_masteries = [m for m in masteries if 50.0 <= m.mastery_score < 75.0]
        for dm in developing_masteries[:2]:
            topic = topic_map.get(dm.topic_id)
            if not topic:
                continue

            lesson = last_lesson_by_topic.get(topic.id) or first_lesson_by_topic.get(topic.id)

            rec = Recommendation(
                user_id=user_id,
                topic_id=topic.id,
                lesson_id=lesson.id if lesson else None,
                title=f"Skill Reinforcement: {topic.title}",
                what_description=f"Level up '{topic.title}' from Developing ({dm.mastery_score}%) to Proficient.",
                why_description=(
                    f"You have a solid base in {topic.title}, but your confidence is at {round(dm.confidence * 100)}%. "
                    f"A brief practice session will solidify your understanding into long-term memory."
                ),
                evidence_description=(
                    f"You have completed {dm.attempts_count} practice sessions with {dm.correct_answers} correct answers. "
                    f"Mistakes are isolated to edge-case scenarios."
                ),
                action_description=f"Take a targeted practice quiz and ask the AI Tutor for hints on edge-case scenarios.",
                priority=RecommendationPriority.MEDIUM,
                recommendation_type=RecommendationType.PRACTICE_QUIZ,
                difficulty=QuestionDifficulty.MEDIUM,
                estimated_duration_minutes=20,
            )
            recommendations.append(rec)

        # 3. Identify unlocked next topics based on prerequisites
        mastered_topic_ids = {m.topic_id for m in masteries if m.mastery_score >= 65.0}
        studied_topic_ids = {m.topic_id for m in masteries}

        for topic in all_topics:
            if topic.id in studied_topic_ids:
                continue
            
            prereq_ids = safe_prereqs.get(topic.id, [])
            all_prereqs_met = all(pid in mastered_topic_ids for pid in prereq_ids)

            if all_prereqs_met:
                first_lesson = first_lesson_by_topic.get(topic.id)

                rec = Recommendation(
                    user_id=user_id,
                    topic_id=topic.id,
                    lesson_id=first_lesson.id if first_lesson else None,
                    title=f"Next Milestone: {topic.title}",
                    what_description=f"Begin learning '{topic.title}' as the next step in your curriculum roadmap.",
                    why_description=(
                        f"All prerequisites for '{topic.title}' have been comfortably mastered with >= 65% proficiency. "
                        f"You are academically ready to advance without gaps."
                    ),
                    evidence_description="Prerequisite mastery requirements satisfied across prerequisite topics.",
                    action_description=f"Complete the introductory lesson '{first_lesson.title if first_lesson else topic.title}'.",
                    priority=RecommendationPriority.MEDIUM,
                    recommendation_type=RecommendationType.NEXT_TOPIC,
                    difficulty=QuestionDifficulty.EASY,
                    estimated_duration_minutes=30,
                )
                recommendations.append(rec)
                break  # Pick top unlocked topic

        # 4. Spaced repetition / decay prevention check
        stale_threshold = datetime.utcnow() - timedelta(days=5)
        stale_masteries = [
            m for m in masteries
            if m.last_practiced_at < stale_threshold and m.mastery_score >= 70.0
        ]
        if stale_masteries:
            stale = stale_masteries[0]
            topic = topic_map.get(stale.topic_id)
            if topic:
                rec = Recommendation(
                    user_id=user_id,
                    topic_id=topic.id,
                    lesson_id=None,
                    title=f"Spaced Retention: {topic.title}",
                    what_description=f"Quick refresher on '{topic.title}' to counteract the forgetting curve.",
                    why_description=(
                        f"You haven't practiced this topic in {(datetime.utcnow() - stale.last_practiced_at).days} days. "
                        f"Spaced retrieval strengthens neural retention by up to 200%."
                    ),
                    evidence_description=f"Last practiced on {stale.last_practiced_at.strftime('%b %d')}. Prior score was {stale.mastery_score}%.",
                    action_description="Take a quick 3-question retention challenge.",
                    priority=RecommendationPriority.LOW,
                    recommendation_type=RecommendationType.CHALLENGE,
                    difficulty=QuestionDifficulty.HARD if stale.mastery_score >= 80 else QuestionDifficulty.MEDIUM,
                    estimated_duration_minutes=10,
                )
                recommendations.append(rec)

        # Fallback if no specific recommendations generated
        if not recommendations and all_topics:
            first_topic = all_topics[0]
            first_lesson = first_lesson_by_topic.get(first_topic.id)
            rec = Recommendation(
                user_id=user_id,
                topic_id=first_topic.id,
                lesson_id=first_lesson.id if first_lesson else None,
                title=f"Kickstart Your Learning: {first_topic.title}",
                what_description=f"Explore your first module '{first_topic.title}'.",
                why_description="Establishing early study momentum builds strong learning habits.",
                evidence_description="New student account detected.",
                action_description="Read the first lesson and complete your initial diagnostic quiz.",
                priority=RecommendationPriority.HIGH,
                recommendation_type=RecommendationType.NEXT_TOPIC,
                difficulty=QuestionDifficulty.EASY,
                estimated_duration_minutes=20,
            )
            recommendations.append(rec)

        for r in recommendations:
            db.add(r)
        db.commit()

        for r in recommendations:
            db.refresh(r)

        return recommendations
