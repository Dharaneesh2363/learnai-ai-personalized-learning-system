from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.assessment import (
    Question,
    QuestionDifficulty,
    Quiz,
    QuizAnswer,
    QuizAttempt,
    QuizQuestion,
)
from app.models.mastery import TopicMastery, LearningEvent, LearningEventType
from app.services.mastery_service import MasteryEngine


class AdaptiveQuizService:
    """
    Intelligent Adaptive Quiz Engine.
    Adapts question difficulty in real-time based on student mastery and live answers.
    """

    DIFFICULTY_PROGRESSION = {
        QuestionDifficulty.EASY: 0,
        QuestionDifficulty.MEDIUM: 1,
        QuestionDifficulty.HARD: 2,
    }

    LEVEL_TO_DIFF = [
        QuestionDifficulty.EASY,
        QuestionDifficulty.MEDIUM,
        QuestionDifficulty.HARD,
    ]

    DIFFICULTY_POINTS = {
        QuestionDifficulty.EASY: 1.0,
        QuestionDifficulty.MEDIUM: 2.0,
        QuestionDifficulty.HARD: 3.0,
    }

    @classmethod
    def get_initial_difficulty(cls, db: Session, user_id: int, topic_id: Optional[int]) -> QuestionDifficulty:
        """Determines initial starting difficulty from student's historical mastery."""
        if not topic_id:
            return QuestionDifficulty.MEDIUM

        mastery = (
            db.query(TopicMastery)
            .filter(TopicMastery.user_id == user_id, TopicMastery.topic_id == topic_id)
            .first()
        )
        if not mastery:
            return QuestionDifficulty.EASY

        if mastery.mastery_score >= 75.0:
            return QuestionDifficulty.HARD
        elif mastery.mastery_score >= 45.0:
            return QuestionDifficulty.MEDIUM
        return QuestionDifficulty.EASY

    @classmethod
    def select_next_question(
        cls,
        db: Session,
        quiz: Quiz,
        target_difficulty: QuestionDifficulty,
        answered_question_ids: List[int],
        weak_concepts: List[str]
    ) -> Optional[Question]:
        """
        Picks the optimal next question:
        1. Must belong to the quiz's topic (or course questions) and NOT be answered yet.
        2. First priority: Matches target difficulty and addresses a known weak concept.
        3. Second priority: Matches target difficulty.
        4. Fallback: Any unanswered question available.
        """
        # Base query for candidate questions
        query = db.query(Question).filter(~Question.id.in_(answered_question_ids))
        if quiz.topic_id:
            query = query.filter(Question.topic_id == quiz.topic_id)
        elif quiz.quiz_questions:
            quiz_q_ids = [qq.question_id for qq in quiz.quiz_questions]
            query = query.filter(Question.id.in_(quiz_q_ids))

        candidates = query.all()
        if not candidates:
            return None

        # 1. Matching difficulty & weak concept
        if weak_concepts:
            for q in candidates:
                if q.difficulty == target_difficulty and q.concept_tag in weak_concepts:
                    return q

        # 2. Matching target difficulty
        for q in candidates:
            if q.difficulty == target_difficulty:
                return q

        # 3. Fallback: Closest difficulty
        target_idx = cls.DIFFICULTY_PROGRESSION[target_difficulty]
        candidates.sort(key=lambda q: abs(cls.DIFFICULTY_PROGRESSION[q.difficulty] - target_idx))
        return candidates[0]

    @classmethod
    def start_quiz_attempt(
        cls,
        db: Session,
        user_id: int,
        quiz_id: int
    ) -> Tuple[QuizAttempt, Optional[Question]]:
        """Initializes a new quiz attempt and selects the first question."""
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise ValueError("Quiz not found")

        initial_difficulty = cls.get_initial_difficulty(db, user_id, quiz.topic_id)

        # Retrieve weak concepts if available
        weak_concepts = []
        if quiz.topic_id:
            mastery = (
                db.query(TopicMastery)
                .filter(TopicMastery.user_id == user_id, TopicMastery.topic_id == quiz.topic_id)
                .first()
            )
            if mastery and mastery.weak_concepts:
                weak_concepts = mastery.weak_concepts

        first_question = cls.select_next_question(
            db=db,
            quiz=quiz,
            target_difficulty=initial_difficulty,
            answered_question_ids=[],
            weak_concepts=weak_concepts
        )

        attempt = QuizAttempt(
            quiz_id=quiz.id,
            user_id=user_id,
            score=0.0,
            max_score=0.0,
            percentage=0.0,
            passed=False,
            is_completed=False,
            current_difficulty=initial_difficulty,
            started_at=datetime.utcnow()
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        # Record learning event
        event = LearningEvent(
            user_id=user_id,
            event_type=LearningEventType.QUIZ_STARTED,
            entity_type="quiz",
            entity_id=quiz.id,
            event_data={"attempt_id": attempt.id, "initial_difficulty": initial_difficulty.value}
        )
        db.add(event)
        db.commit()

        return attempt, first_question

    @classmethod
    def submit_step(
        cls,
        db: Session,
        user_id: int,
        attempt_id: int,
        question_id: int,
        selected_answer: str,
        time_spent_seconds: int = 0
    ) -> dict:
        """
        Authoritative validation of single step, live difficulty shifting,
        and next question selection.
        """
        attempt = db.query(QuizAttempt).filter(
            QuizAttempt.id == attempt_id,
            QuizAttempt.user_id == user_id
        ).first()
        if not attempt:
            raise ValueError("Attempt not found")
        if attempt.is_completed:
            raise ValueError("Quiz attempt already finished")

        quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise ValueError("Question not found")

        # Anti-cheat / Idempotency: Prevent answering the exact same question twice in one attempt
        duplicate_answer = (
            db.query(QuizAnswer)
            .filter(QuizAnswer.attempt_id == attempt.id, QuizAnswer.question_id == question.id)
            .first()
        )
        if duplicate_answer:
            raise ValueError("This question has already been answered for this attempt")

        # Authoritative scoring
        is_correct = (selected_answer.strip().upper() == question.correct_answer.strip().upper())
        points = cls.DIFFICULTY_POINTS.get(question.difficulty, 1.0) if is_correct else 0.0

        # Record answer
        quiz_answer = QuizAnswer(
            attempt_id=attempt.id,
            question_id=question.id,
            selected_answer=selected_answer,
            is_correct=is_correct,
            points_awarded=points,
            time_spent_seconds=time_spent_seconds,
            created_at=datetime.utcnow()
        )
        db.add(quiz_answer)
        db.flush()

        # Fetch all answers for this attempt so far
        past_answers = (
            db.query(QuizAnswer)
            .filter(QuizAnswer.attempt_id == attempt.id)
            .order_by(QuizAnswer.created_at)
            .all()
        )
        answered_ids = [a.question_id for a in past_answers]

        # Adaptive Difficulty Shifting Logic
        current_idx = cls.DIFFICULTY_PROGRESSION[attempt.current_difficulty]
        if is_correct:
            # Check recent consecutive correct
            consecutive_correct = 0
            for a in reversed(past_answers):
                if a.is_correct:
                    consecutive_correct += 1
                else:
                    break
            
            # If 2 consecutive correct, level up difficulty
            if consecutive_correct >= 2 and current_idx < 2:
                current_idx += 1
            elif consecutive_correct >= 1 and current_idx == 0:
                current_idx += 1
        else:
            # Demote difficulty on error if above EASY
            if current_idx > 0:
                current_idx -= 1

        # Strictly clamp bounds [0, 2]
        current_idx = max(0, min(2, current_idx))
        new_difficulty = cls.LEVEL_TO_DIFF[current_idx]
        attempt.current_difficulty = new_difficulty

        # Determine if quiz is completed
        # Adaptive quiz targets 5 questions; or if no more questions available
        target_total_questions = 5 if quiz.is_adaptive else max(5, len(quiz.quiz_questions))
        is_finished = len(answered_ids) >= target_total_questions

        next_q = None
        if not is_finished:
            # Lookup weak concepts
            weak_concepts = []
            if quiz.topic_id:
                mastery = (
                    db.query(TopicMastery)
                    .filter(TopicMastery.user_id == user_id, TopicMastery.topic_id == quiz.topic_id)
                    .first()
                )
                if mastery and mastery.weak_concepts:
                    weak_concepts = mastery.weak_concepts

            next_q = cls.select_next_question(
                db=db,
                quiz=quiz,
                target_difficulty=new_difficulty,
                answered_question_ids=answered_ids,
                weak_concepts=weak_concepts
            )
            if not next_q:
                is_finished = True

        if is_finished:
            # Finalize attempt with bulk question lookup
            total_earned = sum(a.points_awarded for a in past_answers)
            all_questions = db.query(Question).filter(Question.id.in_(answered_ids)).all()
            q_diff_map = {q.id: q.difficulty for q in all_questions}
            
            # Maximum achievable points based on questions encountered
            max_possible = sum(cls.DIFFICULTY_POINTS.get(
                q_diff_map.get(a.question_id, QuestionDifficulty.EASY), 1.0
            ) for a in past_answers)
            
            pct = (total_earned / max(1.0, max_possible)) * 100.0
            attempt.score = round(total_earned, 1)
            attempt.max_score = round(max_possible, 1)
            attempt.percentage = round(pct, 1)
            attempt.passed = pct >= quiz.passing_score
            attempt.is_completed = True
            attempt.completed_at = datetime.utcnow()

            # Trigger Mastery Engine update
            if quiz.topic_id:
                MasteryEngine.update_topic_mastery_from_attempt(
                    db=db,
                    user_id=user_id,
                    topic_id=quiz.topic_id,
                    attempt=attempt,
                    answers=past_answers
                )

            # Record completion learning event
            event = LearningEvent(
                user_id=user_id,
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

        return {
            "is_correct": is_correct,
            "explanation": question.explanation,
            "correct_answer": question.correct_answer,
            "current_difficulty": new_difficulty,
            "next_question": next_q,
            "is_completed": is_finished,
            "questions_answered": len(answered_ids),
            "total_questions": target_total_questions
        }
