from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.models.tutor import MessageRole


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: MessageRole
    content: str
    metadata_json: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    topic_id: Optional[int] = None
    course_id: Optional[int] = None
    topic_title: Optional[str] = None
    course_title: Optional[str] = None
    title: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse] = []

    class Config:
        from_attributes = True


class ChatSessionSummary(BaseModel):
    id: int
    topic_id: Optional[int] = None
    title: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class TutorAskRequest(BaseModel):
    session_id: Optional[int] = None
    topic_id: Optional[int] = None
    course_id: Optional[int] = None
    message: str


class TutorAskResponse(BaseModel):
    session_id: int
    reply: str
    hints: List[str] = []
    follow_up_questions: List[str] = []
    metadata: Dict[str, Any] = {}
