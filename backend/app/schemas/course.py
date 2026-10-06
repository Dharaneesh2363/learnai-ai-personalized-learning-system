from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.models.course import CourseDifficulty, ResourceType


class ResourceBase(BaseModel):
    title: str
    resource_type: ResourceType = ResourceType.DOCUMENT
    url: Optional[str] = None
    content: Optional[str] = None


class ResourceCreate(ResourceBase):
    lesson_id: int


class ResourceResponse(ResourceBase):
    id: int
    lesson_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class LessonBase(BaseModel):
    title: str
    slug: str
    content_markdown: str
    order_index: int = 0
    duration_minutes: int = 15
    is_published: bool = True


class LessonCreate(LessonBase):
    topic_id: int


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    content_markdown: Optional[str] = None
    order_index: Optional[int] = None
    duration_minutes: Optional[int] = None
    is_published: Optional[bool] = None


class LessonSummary(BaseModel):
    id: int
    topic_id: int
    title: str
    slug: str
    order_index: int
    duration_minutes: int
    is_published: bool

    class Config:
        from_attributes = True


class LessonResponse(LessonBase):
    id: int
    topic_id: int
    created_at: datetime
    updated_at: datetime
    resources: List[ResourceResponse] = []

    class Config:
        from_attributes = True


class TopicPrerequisiteResponse(BaseModel):
    prerequisite_topic_id: int
    prerequisite_title: Optional[str] = None

    class Config:
        from_attributes = True


class TopicBase(BaseModel):
    title: str
    slug: str
    description: Optional[str] = None
    order_index: int = 0
    estimated_minutes: int = 30


class TopicCreate(TopicBase):
    module_id: int


class TopicUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    order_index: Optional[int] = None
    estimated_minutes: Optional[int] = None


class TopicSummary(TopicBase):
    id: int
    module_id: int
    lesson_count: int = 0

    class Config:
        from_attributes = True


class TopicResponse(TopicBase):
    id: int
    module_id: int
    created_at: datetime
    updated_at: datetime
    lessons: List[LessonSummary] = []
    prerequisites: List[TopicPrerequisiteResponse] = []

    class Config:
        from_attributes = True


class ModuleBase(BaseModel):
    title: str
    description: Optional[str] = None
    order_index: int = 0


class ModuleCreate(ModuleBase):
    course_id: int


class ModuleResponse(ModuleBase):
    id: int
    course_id: int
    created_at: datetime
    updated_at: datetime
    topics: List[TopicResponse] = []

    class Config:
        from_attributes = True


class CourseBase(BaseModel):
    title: str
    slug: str
    description: Optional[str] = None
    category: str = "Computer Science"
    difficulty: CourseDifficulty = CourseDifficulty.BEGINNER
    thumbnail_url: Optional[str] = None
    is_published: bool = True


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[CourseDifficulty] = None
    thumbnail_url: Optional[str] = None
    is_published: Optional[bool] = None


class CourseResponse(CourseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CourseDetailResponse(CourseResponse):
    modules: List[ModuleResponse] = []
