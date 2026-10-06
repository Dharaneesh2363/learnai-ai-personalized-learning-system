import uuid
import pytest
from fastapi.testclient import TestClient
from app.models.assessment import Question, QuestionDifficulty, QuestionType, Quiz
from app.models.course import Course, CourseDifficulty, Lesson, Module, Topic
from app.models.mastery import TopicMastery, MasteryLevel


def test_full_student_journey_golden_path(client: TestClient, db_session):
    """
    End-to-End integration test covering the entire student journey:
    1. Register
    2. Login
    3. View Course Catalog & Lessons
    4. Take Adaptive Quiz
    5. Check Mastery Update
    6. Inspect 4-Pillar Recommendations
    7. Complete Recommendation
    8. Converse with AI Tutor
    9. Review Dashboard Analytics
    """
    uid = uuid.uuid4().hex[:6]
    student_email = f"sarah_{uid}@learnai.dev"

    # 1. Register student
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": student_email,
            "password": "Password123!",
            "full_name": "Sarah Connor",
        }
    )
    assert reg_resp.status_code == 201
    auth_data = reg_resp.json()
    token = auth_data["access_token"]
    user_id = auth_data["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Verify Profile
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == student_email

    # Setup Course, Module, Topic, Lesson, and Adaptive Quiz in DB
    course = Course(title="Fullstack Integration Course", slug=f"fullstack-integ-{uid}", difficulty=CourseDifficulty.BEGINNER)
    db_session.add(course)
    db_session.commit()

    module = Module(course_id=course.id, title="Basics Module", order_index=1)
    db_session.add(module)
    db_session.commit()

    topic = Topic(module_id=module.id, title="State Management", slug=f"state-management-{uid}", order_index=1)
    db_session.add(topic)
    db_session.commit()

    lesson = Lesson(topic_id=topic.id, title="Hooks & Reducers", slug="hooks-reducers", content_markdown="Use useState for local state.", order_index=1)
    db_session.add(lesson)
    db_session.commit()

    # Create questions
    for i in range(1, 6):
        q = Question(
            topic_id=topic.id,
            question_text=f"State Question {i}?",
            explanation="State updates trigger re-renders.",
            difficulty=QuestionDifficulty.EASY if i <= 2 else QuestionDifficulty.MEDIUM,
            question_type=QuestionType.MULTIPLE_CHOICE,
            options_json=[{"id": "A", "text": "Correct"}, {"id": "B", "text": "Wrong"}],
            correct_answer="A",
            concept_tag="state_hooks",
            points=1 if i <= 2 else 2
        )
        db_session.add(q)
    db_session.commit()

    quiz = Quiz(
        course_id=course.id,
        topic_id=topic.id,
        title="State Management Quiz",
        is_adaptive=True,
        passing_score=60.0
    )
    db_session.add(quiz)
    db_session.commit()

    # 3. View Courses
    courses_resp = client.get("/api/v1/courses", headers=headers)
    assert courses_resp.status_code == 200
    assert len(courses_resp.json()) >= 1

    # 4. Start Adaptive Quiz
    start_resp = client.post(f"/api/v1/quizzes/{quiz.id}/start-attempt", headers=headers)
    assert start_resp.status_code == 200
    attempt_id = start_resp.json()["id"]

    # Retrieve initial question
    take_resp = client.get(f"/api/v1/quizzes/{quiz.id}/take", headers=headers)
    assert take_resp.status_code == 200
    current_q_id = take_resp.json()["questions"][0]["id"]

    # Step through 5 questions
    for step in range(5):
        ans_resp = client.post(
            "/api/v1/quizzes/adaptive-step",
            headers=headers,
            json={
                "attempt_id": attempt_id,
                "question_id": current_q_id,
                "selected_answer": "A",
                "time_spent_seconds": 12
            }
        )
        assert ans_resp.status_code == 200
        step_data = ans_resp.json()
        assert step_data["is_correct"] is True
        if step_data["is_completed"]:
            break
        current_q_id = step_data["next_question"]["id"]

    # Inspect final attempt detail
    detail_resp = client.get(f"/api/v1/quizzes/attempts/{attempt_id}", headers=headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["is_completed"] is True
    assert detail["passed"] is True
    assert len(detail["answers"]) > 0

    # 5. Verify Topic Mastery
    mastery_resp = client.get("/api/v1/mastery/summary", headers=headers)
    assert mastery_resp.status_code == 200
    m_data = mastery_resp.json()
    assert m_data["overall_mastery"] > 0
    assert m_data["total_topics"] >= 1

    # 6. Verify 4-Pillar Recommendations
    rec_resp = client.get("/api/v1/recommendations?refresh=true", headers=headers)
    assert rec_resp.status_code == 200
    recs = rec_resp.json()
    assert len(recs) >= 1
    top_rec = recs[0]
    assert "what_description" in top_rec
    assert "why_description" in top_rec
    assert "evidence_description" in top_rec
    assert "action_description" in top_rec

    # 7. Complete Recommendation
    act_resp = client.post(
        f"/api/v1/recommendations/{top_rec['id']}/action",
        headers=headers,
        json={"is_completed": True}
    )
    assert act_resp.status_code == 200
    assert act_resp.json()["is_completed"] is True

    # 8. Converse with AI Tutor
    tutor_resp = client.post(
        "/api/v1/tutor/ask",
        headers=headers,
        json={
            "topic_id": topic.id,
            "message": "Can you explain how useState triggers re-renders?"
        }
    )
    assert tutor_resp.status_code == 200
    t_data = tutor_resp.json()
    assert len(t_data["reply"]) > 0
    assert len(t_data["hints"]) > 0

    # 9. Review Dashboard Analytics
    analytics_resp = client.get("/api/v1/analytics/dashboard", headers=headers)
    assert analytics_resp.status_code == 200
    a_data = analytics_resp.json()
    assert a_data["overall_mastery"] > 0
    assert a_data["quizzes_taken"] >= 1
    assert len(a_data["mastery_by_topic"]) >= 1
