from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.assessment import Question, QuestionDifficulty, QuizAnswer, QuizAttempt
from app.models.mastery import MasteryLevel, MasteryTrend, TopicMastery


class MasteryEngine:
    """
    Transparent, explainable Knowledge & Mastery modeling engine.
    
    Formula:
    1. Historical accuracy: total correct / total answered
    2. Recent accuracy: latest attempt score percentage
    3. Dual-window blend: 0.35 * Historical + 0.65 * Recent
    4. Difficulty adjustment: bonus for hard question success, penalty for easy failures
    5. Spaced decay: Ebbinghaus forgetting decay when days_since_practice > 5
    6. Confidence: asymptotic function of total questions answered
    """

    @staticmethod
    def calculate_level(score: float) -> MasteryLevel:
        if score >= 80.0:
            return MasteryLevel.MASTERED
        elif score >= 60.0:
            return MasteryLevel.PROFICIENT
        elif score >= 40.0:
            return MasteryLevel.DEVELOPING
        return MasteryLevel.BEGINNER

    @staticmethod
    def get_recommended_difficulty(score: float) -> QuestionDifficulty:
        if score >= 75.0:
            return QuestionDifficulty.HARD
        elif score >= 50.0:
            return QuestionDifficulty.MEDIUM
        return QuestionDifficulty.EASY

    @classmethod
    def update_topic_mastery_from_attempt(
        cls,
        db: Session,
        user_id: int,
        topic_id: int,
        attempt: QuizAttempt,
        answers: List[QuizAnswer]
    ) -> TopicMastery:
        """Update mastery for a topic following a quiz attempt."""
        mastery = (
            db.query(TopicMastery)
            .filter(TopicMastery.user_id == user_id, TopicMastery.topic_id == topic_id)
            .first()
        )

        if not mastery:
            mastery = TopicMastery(
                user_id=user_id,
                topic_id=topic_id,
                mastery_score=0.0,
                confidence=0.1,
                attempts_count=0,
                correct_answers=0,
                incorrect_answers=0,
                last_practiced_at=datetime.utcnow(),
                trend=MasteryTrend.STABLE,
                current_difficulty=QuestionDifficulty.EASY,
                weak_concepts=[],
                strong_concepts=[]
            )
            db.add(mastery)
            db.flush()

        # Gather attempt statistics
        attempt_correct = sum(1 for a in answers if a.is_correct)
        attempt_incorrect = len(answers) - attempt_correct
        recent_accuracy = (attempt_correct / len(answers) * 100.0) if answers else 0.0

        # Update lifetime counters
        old_score = mastery.mastery_score
        mastery.attempts_count += 1
        mastery.correct_answers += attempt_correct
        mastery.incorrect_answers += attempt_incorrect
        total_answers = mastery.correct_answers + mastery.incorrect_answers
        historical_accuracy = (mastery.correct_answers / total_answers * 100.0) if total_answers > 0 else 0.0

        # Dual-window weighted blend (recent 65%, historical 35%)
        blended_score = (0.35 * historical_accuracy) + (0.65 * recent_accuracy)

        # Difficulty weighting modifier
        # Hard questions reward extra mastery; easy questions have standard reward
        difficulty_multipliers = {
            QuestionDifficulty.EASY: 0.95,
            QuestionDifficulty.MEDIUM: 1.0,
            QuestionDifficulty.HARD: 1.08
        }
        mult = difficulty_multipliers.get(attempt.current_difficulty, 1.0)
        adjusted_score = min(100.0, max(0.0, blended_score * mult))

        # Confidence calculation based on question volume (approaches 1.0 as questions count reaches 20+)
        confidence = min(0.99, max(0.15, total_answers / 20.0))

        # Trend detection
        score_diff = adjusted_score - old_score
        if score_diff >= 4.0:
            trend = MasteryTrend.IMPROVING
        elif score_diff <= -4.0:
            trend = MasteryTrend.DECLINING
        else:
            trend = MasteryTrend.STABLE

        # Extract weak and strong concepts from question concept_tags
        weak_set = set(mastery.weak_concepts or [])
        strong_set = set(mastery.strong_concepts or [])

        # Batch query questions to avoid N+1 queries
        q_ids = [ans.question_id for ans in answers]
        questions_map = {}
        if q_ids:
            questions = db.query(Question).filter(Question.id.in_(q_ids)).all()
            questions_map = {q.id: q for q in questions}

        for ans in answers:
            q = questions_map.get(ans.question_id)
            if q and q.concept_tag:
                tag = q.concept_tag.strip()
                if ans.is_correct:
                    if tag in weak_set:
                        weak_set.remove(tag)
                    strong_set.add(tag)
                else:
                    if tag in strong_set:
                        strong_set.remove(tag)
                    weak_set.add(tag)

        # Update mastery model fields
        mastery.mastery_score = round(adjusted_score, 1)
        mastery.confidence = round(confidence, 2)
        mastery.last_practiced_at = datetime.utcnow()
        mastery.trend = trend
        mastery.current_difficulty = cls.get_recommended_difficulty(adjusted_score)
        mastery.weak_concepts = list(weak_set)
        mastery.strong_concepts = list(strong_set)
        mastery.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(mastery)
        return mastery

    @classmethod
    def apply_decay(cls, mastery: TopicMastery) -> float:
        """
        Calculates time-decayed mastery score if inactive for multiple days.
        Decays up to 20% over 30 days of inactivity according to Ebbinghaus forgetting curve.
        """
        if not mastery.last_practiced_at:
            return mastery.mastery_score
        days_inactive = (datetime.utcnow() - mastery.last_practiced_at).days
        if days_inactive > 7:
            decay_factor = max(0.80, 1.0 - (0.01 * min(days_inactive - 7, 20)))
            return round(mastery.mastery_score * decay_factor, 1)
        return mastery.mastery_score

    @classmethod
    def apply_decay_if_needed(cls, db: Session, mastery: TopicMastery) -> float:
        """
        Calculates and persists time-decayed mastery score if inactive for multiple days.
        Decays up to 20% over 30 days of inactivity according to Ebbinghaus forgetting curve.
        """
        if not mastery.last_practiced_at:
            return mastery.mastery_score
        days_inactive = (datetime.utcnow() - mastery.last_practiced_at).days
        if days_inactive > 7:
            decay_factor = max(0.80, 1.0 - (0.01 * min(days_inactive - 7, 20)))
            decayed_score = round(mastery.mastery_score * decay_factor, 1)
            if decayed_score != mastery.mastery_score:
                mastery.mastery_score = decayed_score
                mastery.current_difficulty = cls.get_recommended_difficulty(decayed_score)
                mastery.updated_at = datetime.utcnow()
                db.add(mastery)
                db.commit()
                db.refresh(mastery)
            return decayed_score
        return mastery.mastery_score
