import pytest
from fastapi.testclient import TestClient
from app.core.security import create_access_token
from app.models.course import Course, CourseDifficulty, Lesson, Module, Topic, TopicPrerequisite
from app.models.user import User
from app.services.ai.factory import get_ai_provider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.mock_provider import MockAIProvider
from app.services.ai.openai_provider import OpenAIProvider
from app.services.content_retriever import LearningContextRetriever


@pytest.fixture
def retriever_fixture(db_session):
    """Sets up course with modules, topics, prerequisites, and markdown lessons."""
    import uuid
    uid = uuid.uuid4().hex[:6]
    course = Course(
        title="Python Data Engineering",
        slug=f"python-data-eng-{uid}",
        difficulty=CourseDifficulty.INTERMEDIATE
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    module = Module(course_id=course.id, title="Core Pipelines", order_index=1)
    db_session.add(module)
    db_session.commit()
    db_session.refresh(module)

    # Prerequisite topic: Generators
    t_prereq = Topic(
        module_id=module.id,
        title="Python Generators",
        slug=f"python-generators-{uid}",
        description="Iterators and yield statements for memory efficiency",
        order_index=1
    )
    db_session.add(t_prereq)

    # Target topic: Async Pipelines
    t_target = Topic(
        module_id=module.id,
        title="Async Stream Pipelines",
        slug=f"async-stream-pipelines-{uid}",
        description="Concurrency using asyncio streams and event loops",
        order_index=2
    )
    db_session.add(t_target)
    db_session.commit()
    db_session.refresh(t_prereq)
    db_session.refresh(t_target)

    # Link prerequisite
    prereq_link = TopicPrerequisite(
        topic_id=t_target.id,
        prerequisite_topic_id=t_prereq.id
    )
    db_session.add(prereq_link)

    # Add lesson
    lesson = Lesson(
        topic_id=t_target.id,
        title="Mastering Async Iterators",
        slug="mastering-async-iterators",
        content_markdown="# Async Iterators\nUse `async for` to stream records without blocking the event loop.",
        order_index=1,
        is_published=True
    )
    db_session.add(lesson)
    db_session.commit()
    db_session.refresh(lesson)

    return {"topic": t_target, "prereq": t_prereq, "lesson": lesson}


def test_learning_context_retriever_extracts_curriculum(db_session, retriever_fixture):
    """Verify LearningContextRetriever retrieves lessons and prerequisite metadata."""
    topic = retriever_fixture["topic"]
    context = LearningContextRetriever.retrieve_context_for_topic(
        db=db_session,
        topic_id=topic.id,
        include_prerequisites=True
    )

    assert context["topic_title"] == "Async Stream Pipelines"
    assert len(context["snippets"]) == 1
    assert "Mastering Async Iterators" in context["snippets"][0]["lesson_title"]
    assert "async for" in context["snippets"][0]["snippet"]
    assert len(context["prerequisites"]) == 1
    assert context["prerequisites"][0]["title"] == "Python Generators"
    assert "## Course Context" in context["grounding_text"]


def test_learning_context_retriever_query_matching(db_session, retriever_fixture):
    """Verify lexical query keyword search across lessons."""
    query_result = LearningContextRetriever.retrieve_context_for_query(
        db=db_session,
        query="stream records event loop",
        topic_id=retriever_fixture["topic"].id
    )
    assert "Mastering Async Iterators" in query_result
    assert "async for" in query_result


def test_ai_provider_fallbacks_and_mock():
    """Verify MockAIProvider and graceful degradation of cloud providers."""
    mock = MockAIProvider()
    reply = mock.generate_text("Explain loops")
    assert "loop" in reply.lower() or "iteration" in reply.lower()

    chat = mock.generate_chat_response(
        messages=[{"role": "user", "content": "Help me with lists"}],
        system_instruction="Teach gently"
    )
    assert "reply" in chat
    assert len(chat["hints"]) > 0
    assert len(chat["follow_up_questions"]) > 0

    questions = mock.generate_questions("Python Lists", "medium", ["indexing"])
    assert len(questions) > 0
    assert "options_json" in questions[0]
    assert "correct_answer" in questions[0]

    # Verify GeminiProvider gracefully falls back
    gemini = GeminiProvider(api_key="mock_key")
    gemini_res = gemini.generate_text("Explain recursion")
    assert len(gemini_res) > 0

    # Verify OpenAIProvider gracefully falls back
    openai = OpenAIProvider(api_key="mock_key")
    openai_res = openai.generate_text("Explain stacks")
    assert len(openai_res) > 0


def test_ai_tutor_api_endpoint_with_grounding(client: TestClient, db_session, test_user: User, retriever_fixture):
    """Verify the /api/v1/tutor/ask endpoint succeeds with RAG grounding."""
    token = create_access_token(subject=test_user.id, role=test_user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        "/api/v1/tutor/ask",
        headers=headers,
        json={
            "topic_id": retriever_fixture["topic"].id,
            "message": "How do async streams work?"
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    assert len(data["reply"]) > 0
    assert "hints" in data
    assert "follow_up_questions" in data
    assert data["session_id"] is not None
