from datetime import datetime
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.course import Course, Topic
from app.models.mastery import LearningEvent, LearningEventType, TopicMastery
from app.models.tutor import ChatMessage, ChatSession, MessageRole
from app.models.user import User
from app.schemas.tutor import (
    ChatMessageResponse,
    ChatSessionResponse,
    ChatSessionSummary,
    TutorAskRequest,
    TutorAskResponse,
)
from app.services.ai.factory import get_ai_provider

router = APIRouter(prefix="/tutor", tags=["AI Contextual Tutor"])


@router.get("/sessions", response_model=List[ChatSessionSummary])
def list_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List student's active tutoring conversations."""
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id, ChatSession.is_active == True)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    return [
        ChatSessionSummary(
            id=s.id,
            topic_id=s.topic_id,
            title=s.title,
            is_active=s.is_active,
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=len(s.messages)
        )
        for s in sessions
    ]


@router.post("/sessions", response_model=ChatSessionResponse)
def create_chat_session(
    topic_id: Optional[int] = None,
    course_id: Optional[int] = None,
    title: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new dedicated tutoring session."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first() if topic_id else None
    session_title = title or (f"Tutoring: {topic.title}" if topic else "General AI Tutor Session")

    session = ChatSession(
        user_id=current_user.id,
        topic_id=topic_id,
        course_id=course_id,
        title=session_title,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Initial friendly welcome message
    welcome_text = (
        f"Hi {current_user.full_name}! I'm your AI Tutor"
        + (f" for **{topic.title}**." if topic else ".")
        + " How can I help you today? Feel free to ask for explanations, code breakdowns, or conceptual hints!"
    )
    welcome_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.ASSISTANT,
        content=welcome_text,
        metadata_json={
            "hints": ["Ask me to explain any line of code", "Ask 'Why does this mistake happen?'"],
            "follow_up_questions": ["What topic are you currently studying?"]
        },
        created_at=datetime.utcnow()
    )
    db.add(welcome_msg)
    db.commit()
    db.refresh(session)

    return session


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def get_session_detail(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Retrieve full chat history for a session."""
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    topic = db.query(Topic).filter(Topic.id == session.topic_id).first() if session.topic_id else None
    course = db.query(Course).filter(Course.id == session.course_id).first() if session.course_id else None

    return ChatSessionResponse(
        id=session.id,
        user_id=session.user_id,
        topic_id=session.topic_id,
        course_id=session.course_id,
        topic_title=topic.title if topic else None,
        course_title=course.title if course else None,
        title=session.title,
        is_active=session.is_active,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[ChatMessageResponse.model_validate(m) for m in session.messages]
    )


@router.post("/ask", response_model=TutorAskResponse)
def ask_tutor(
    req: TutorAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Context-aware AI Tutoring endpoint.
    Aggregates student topic mastery, weak concepts, and chat history.
    """
    session = None
    if req.session_id:
        session = (
            db.query(ChatSession)
            .filter(ChatSession.id == req.session_id, ChatSession.user_id == current_user.id)
            .first()
        )
    
    if not session:
        # Create session on the fly
        topic = db.query(Topic).filter(Topic.id == req.topic_id).first() if req.topic_id else None
        session = ChatSession(
            user_id=current_user.id,
            topic_id=req.topic_id,
            course_id=req.course_id,
            title=f"Tutoring: {topic.title if topic else 'General'}",
            is_active=True
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    # Gather student context
    student_context = {
        "student_name": current_user.full_name,
        "mastery_level": "Developing",
        "mastery_score": 50.0,
        "weak_concepts": [],
        "strong_concepts": [],
        "topic_title": session.topic.title if session.topic else "General Programming"
    }

    if session.topic_id:
        mastery = (
            db.query(TopicMastery)
            .filter(TopicMastery.user_id == current_user.id, TopicMastery.topic_id == session.topic_id)
            .first()
        )
        if mastery:
            student_context["mastery_level"] = mastery.level.value
            student_context["mastery_score"] = mastery.mastery_score
            student_context["weak_concepts"] = mastery.weak_concepts or []
            student_context["strong_concepts"] = mastery.strong_concepts or []

        # RAG grounding from curriculum lessons
        from app.services.content_retriever import LearningContextRetriever
        rag_context = LearningContextRetriever.retrieve_context_for_topic(
            db=db, topic_id=session.topic_id, max_lessons=2
        )
        student_context["curriculum_grounding"] = rag_context.get("grounding_text", "")

    # Record student question in database
    user_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.USER,
        content=req.message,
        metadata_json={},
        created_at=datetime.utcnow()
    )
    db.add(user_msg)
    session.updated_at = datetime.utcnow()
    db.commit()

    # Build conversation history
    past_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    history_payload = [
        {"role": m.role.value, "content": m.content}
        for m in past_messages[-8:]  # Last 8 turns for context
    ]

    # Generate response from AI Provider
    ai_provider = get_ai_provider()
    system_instruction = (
        "You are an encouraging, pedagogical AI Tutor for LearnAI. Teach step-by-step with practical examples. "
        "Ground your explanations in the provided course curriculum and lessons. "
        "Avoid giving straight copy-paste answers immediately; guide the student through Socratic questions and hints. "
        "Keep language clear, concise, and friendly. Adapt difficulty according to the student's mastery level."
    )
    tutor_output = ai_provider.generate_chat_response(
        messages=history_payload,
        system_instruction=system_instruction,
        student_context=student_context
    )

    # Save assistant response
    assistant_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.ASSISTANT,
        content=tutor_output["reply"],
        metadata_json={
            "hints": tutor_output.get("hints", []),
            "follow_up_questions": tutor_output.get("follow_up_questions", [])
        },
        created_at=datetime.utcnow()
    )
    db.add(assistant_msg)

    # Track learning event
    event = LearningEvent(
        user_id=current_user.id,
        event_type=LearningEventType.AI_QUESTION_ASKED,
        entity_type="chat_session",
        entity_id=session.id,
        event_data={"topic_id": session.topic_id, "query_length": len(req.message)}
    )
    db.add(event)
    db.commit()

    return TutorAskResponse(
        session_id=session.id,
        reply=tutor_output["reply"],
        hints=tutor_output.get("hints", []),
        follow_up_questions=tutor_output.get("follow_up_questions", []),
        metadata=student_context
    )
