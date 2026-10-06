import pytest
from app.models.assessment import QuestionDifficulty
from app.models.mastery import MasteryLevel, MasteryTrend
from app.services.adaptive_quiz_service import AdaptiveQuizService
from app.services.mastery_service import MasteryEngine
from app.services.recommendation_service import RecommendationEngine


def test_mastery_level_tiers():
    assert MasteryEngine.calculate_level(85.0) == MasteryLevel.MASTERED
    assert MasteryEngine.calculate_level(70.0) == MasteryLevel.PROFICIENT
    assert MasteryEngine.calculate_level(50.0) == MasteryLevel.DEVELOPING
    assert MasteryEngine.calculate_level(30.0) == MasteryLevel.BEGINNER


def test_recommended_difficulty():
    assert MasteryEngine.get_recommended_difficulty(85.0) == QuestionDifficulty.HARD
    assert MasteryEngine.get_recommended_difficulty(60.0) == QuestionDifficulty.MEDIUM
    assert MasteryEngine.get_recommended_difficulty(35.0) == QuestionDifficulty.EASY


def test_recommendation_engine_generates_4_factors(db, student_user):
    recs = RecommendationEngine.generate_recommendations_for_user(db, student_user.id)
    assert len(recs) >= 1
    
    first_rec = recs[0]
    # Verify the 4 essential explainability pillars
    assert first_rec.what_description != ""
    assert first_rec.why_description != ""
    assert first_rec.evidence_description != ""
    assert first_rec.action_description != ""
    assert first_rec.priority is not None


def test_adaptive_quiz_initial_difficulty(db, student_user):
    # Topic Loops (id 3) mastery is 42% -> Should start at EASY/MEDIUM
    diff = AdaptiveQuizService.get_initial_difficulty(db, student_user.id, 3)
    assert diff in [QuestionDifficulty.EASY, QuestionDifficulty.MEDIUM]


def test_quiz_client_take_does_not_leak_answers(client, student_auth_headers):
    # Take quiz endpoint should give questions WITHOUT 'correct_answer' or 'explanation'
    response = client.get("/api/v1/quizzes/1/take", headers=student_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "questions" in data
    assert len(data["questions"]) > 0
    q = data["questions"][0]
    assert "correct_answer" not in q
    assert "explanation" not in q
    assert "question_text" in q
    assert "options_json" in q


def test_mastery_summary_api(client, student_auth_headers):
    response = client.get("/api/v1/mastery/summary", headers=student_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "overall_mastery" in data
    assert data["total_topics"] >= 5
    assert len(data["top_weak_topics"]) > 0
    # Alex Chen's weakest topic should include loops or trees or oop
    weakest_slugs = [t["topic_title"] for t in data["top_weak_topics"]]
    assert any("Loops" in s or "Tree" in s or "Object" in s for s in weakest_slugs)
