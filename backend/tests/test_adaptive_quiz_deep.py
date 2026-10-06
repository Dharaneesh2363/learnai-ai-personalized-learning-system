import pytest
from fastapi.testclient import TestClient
from app.core.security import create_access_token
from app.models.assessment import Question, QuestionDifficulty, QuestionType, Quiz, QuizAttempt, QuizQuestion
from app.models.course import Course, CourseDifficulty, Module, Topic
from app.models.mastery import TopicMastery, MasteryLevel
from app.models.user import User, UserRole
from app.services.adaptive_quiz_service import AdaptiveQuizService


@pytest.fixture
def adaptive_quiz_fixture(db_session, test_user: User):
    """Sets up a complete course, topic, questions at all difficulties, and an adaptive quiz."""
    import uuid
    uid = uuid.uuid4().hex[:6]
    course = Course(
        title="Adaptive Test Course",
        slug=f"adaptive-test-course-{uid}",
        difficulty=CourseDifficulty.INTERMEDIATE
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    module = Module(course_id=course.id, title="Core Module", order_index=1)
    db_session.add(module)
    db_session.commit()
    db_session.refresh(module)

    topic = Topic(
        module_id=module.id,
        title="Algorithms & Complexity",
        slug=f"algorithms-complexity-{uid}",
        order_index=1
    )
    db_session.add(topic)
    db_session.commit()
    db_session.refresh(topic)

    # Create questions for EASY, MEDIUM, HARD
    questions = []
    # 3 Easy questions
    for i in range(1, 4):
        q = Question(
            topic_id=topic.id,
            question_text=f"Easy Question {i}",
            explanation=f"Easy explanation {i}",
            difficulty=QuestionDifficulty.EASY,
            question_type=QuestionType.MULTIPLE_CHOICE,
            options_json=[{"id": "A", "text": "Option A"}, {"id": "B", "text": "Option B"}],
            correct_answer="A",
            concept_tag="basics",
            points=1
        )
        questions.append(q)

    # 3 Medium questions
    for i in range(1, 4):
        q = Question(
            topic_id=topic.id,
            question_text=f"Medium Question {i}",
            explanation=f"Medium explanation {i}",
            difficulty=QuestionDifficulty.MEDIUM,
            question_type=QuestionType.MULTIPLE_CHOICE,
            options_json=[{"id": "A", "text": "Option A"}, {"id": "B", "text": "Option B"}],
            correct_answer="A",
            concept_tag="algorithms",
            points=2
        )
        questions.append(q)

    # 3 Hard questions
    for i in range(1, 4):
        q = Question(
            topic_id=topic.id,
            question_text=f"Hard Question {i}",
            explanation=f"Hard explanation {i}",
            difficulty=QuestionDifficulty.HARD,
            question_type=QuestionType.MULTIPLE_CHOICE,
            options_json=[{"id": "A", "text": "Option A"}, {"id": "B", "text": "Option B"}],
            correct_answer="A",
            concept_tag="complexity",
            points=3
        )
        questions.append(q)

    for q in questions:
        db_session.add(q)
    db_session.commit()

    quiz = Quiz(
        course_id=course.id,
        topic_id=topic.id,
        title="Adaptive Algorithms Diagnostic",
        is_adaptive=True,
        passing_score=70.0
    )
    db_session.add(quiz)
    db_session.commit()
    db_session.refresh(quiz)

    return {"course": course, "topic": topic, "quiz": quiz, "questions": questions}


def test_adaptive_quiz_start_and_client_privacy(client: TestClient, db_session, test_user: User, adaptive_quiz_fixture):
    """Verify that starting a quiz creates an attempt with EASY difficulty for beginner student."""
    quiz = adaptive_quiz_fixture["quiz"]
    token = create_access_token(subject=test_user.id, role=test_user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(f"/api/v1/quizzes/{quiz.id}/start-attempt", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["quiz_id"] == quiz.id
    assert data["user_id"] == test_user.id
    assert data["current_difficulty"] == "easy"
    assert data["is_completed"] is False

    # Check that take endpoint does NOT expose correct_answer or explanation
    take_resp = client.get(f"/api/v1/quizzes/{quiz.id}/take", headers=headers)
    assert take_resp.status_code == 200
    take_data = take_resp.json()
    assert len(take_data["questions"]) > 0
    first_q = take_data["questions"][0]
    assert "correct_answer" not in first_q
    assert "explanation" not in first_q


def test_adaptive_difficulty_progression_and_anti_cheat(client: TestClient, db_session, test_user: User, adaptive_quiz_fixture):
    """
    Test live adaptive difficulty progression:
    - Answer 1 correct: stays or goes to medium
    - Answer 2 correct: goes to medium/hard
    - Test that duplicate submission of the same question in same attempt is rejected!
    """
    quiz = adaptive_quiz_fixture["quiz"]
    token = create_access_token(subject=test_user.id, role=test_user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    # Start attempt
    start_resp = client.post(f"/api/v1/quizzes/{quiz.id}/start-attempt", headers=headers)
    attempt_id = start_resp.json()["id"]

    # Retrieve first question
    take_resp = client.get(f"/api/v1/quizzes/{quiz.id}/take", headers=headers)
    q1_id = take_resp.json()["questions"][0]["id"]

    # Submit correct answer for Q1
    step1_resp = client.post(
        "/api/v1/quizzes/adaptive-step",
        headers=headers,
        json={
            "attempt_id": attempt_id,
            "question_id": q1_id,
            "selected_answer": "A",
            "time_spent_seconds": 15
        }
    )
    assert step1_resp.status_code == 200
    s1 = step1_resp.json()
    assert s1["is_correct"] is True
    # Moving up from EASY to MEDIUM
    assert s1["current_difficulty"] in ["medium", "hard"]

    # ANTI-CHEAT TEST: Resubmitting the same question must fail with 400 Bad Request
    dup_resp = client.post(
        "/api/v1/quizzes/adaptive-step",
        headers=headers,
        json={
            "attempt_id": attempt_id,
            "question_id": q1_id,
            "selected_answer": "A",
            "time_spent_seconds": 5
        }
    )
    assert dup_resp.status_code == 400
    assert "already been answered" in dup_resp.json()["detail"].lower()


def test_adaptive_difficulty_demotion_on_mistake(client: TestClient, db_session, test_user: User, adaptive_quiz_fixture):
    """Verify that an incorrect answer reduces difficulty level."""
    quiz = adaptive_quiz_fixture["quiz"]
    topic = adaptive_quiz_fixture["topic"]

    # Pre-seed student mastery at 80% so starting difficulty is HARD
    mastery = TopicMastery(
        user_id=test_user.id,
        topic_id=topic.id,
        mastery_score=80.0,
        confidence=0.8,
        attempts_count=3,
        current_difficulty=QuestionDifficulty.HARD
    )
    db_session.add(mastery)
    db_session.commit()

    token = create_access_token(subject=test_user.id, role=test_user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    # Start attempt: should start at HARD
    start_resp = client.post(f"/api/v1/quizzes/{quiz.id}/start-attempt", headers=headers)
    assert start_resp.json()["current_difficulty"] == "hard"
    attempt_id = start_resp.json()["id"]

    # Find a hard question
    hard_q = [q for q in adaptive_quiz_fixture["questions"] if q.difficulty == QuestionDifficulty.HARD][0]

    # Submit an incorrect answer ("B" when correct is "A")
    step_resp = client.post(
        "/api/v1/quizzes/adaptive-step",
        headers=headers,
        json={
            "attempt_id": attempt_id,
            "question_id": hard_q.id,
            "selected_answer": "B",
            "time_spent_seconds": 20
        }
    )
    assert step_resp.status_code == 200
    res = step_resp.json()
    assert res["is_correct"] is False
    # Demoted from HARD to MEDIUM
    assert res["current_difficulty"] == "medium"
