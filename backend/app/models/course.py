import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class CourseDifficulty(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ResourceType(str, enum.Enum):
    VIDEO = "video"
    DOCUMENT = "document"
    LINK = "link"
    CODE_SANDBOX = "code_sandbox"


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), default="Computer Science", nullable=False)
    difficulty = Column(Enum(CourseDifficulty), default=CourseDifficulty.BEGINNER, nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    is_published = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan", order_by="Module.order_index")
    quizzes = relationship("Quiz", back_populates="course", cascade="all, delete-orphan")


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    course = relationship("Course", back_populates="modules")
    topics = relationship("Topic", back_populates="module", cascade="all, delete-orphan", order_by="Topic.order_index")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0, nullable=False)
    estimated_minutes = Column(Integer, default=30, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    module = relationship("Module", back_populates="topics")
    lessons = relationship("Lesson", back_populates="topic", cascade="all, delete-orphan", order_by="Lesson.order_index")
    questions = relationship("Question", back_populates="topic", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="topic")
    masteries = relationship("TopicMastery", back_populates="topic", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="topic", cascade="all, delete-orphan")
    
    # Prerequisites
    prerequisites = relationship(
        "TopicPrerequisite",
        foreign_keys="TopicPrerequisite.topic_id",
        back_populates="topic",
        cascade="all, delete-orphan"
    )
    required_by = relationship(
        "TopicPrerequisite",
        foreign_keys="TopicPrerequisite.prerequisite_topic_id",
        back_populates="prerequisite_topic",
        cascade="all, delete-orphan"
    )


class TopicPrerequisite(Base):
    __tablename__ = "topic_prerequisites"
    __table_args__ = (
        UniqueConstraint("topic_id", "prerequisite_topic_id", name="uq_topic_prerequisite"),
    )

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    prerequisite_topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    topic = relationship("Topic", foreign_keys=[topic_id], back_populates="prerequisites")
    prerequisite_topic = relationship("Topic", foreign_keys=[prerequisite_topic_id], back_populates="required_by")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), index=True, nullable=False)
    content_markdown = Column(Text, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)
    duration_minutes = Column(Integer, default=15, nullable=False)
    is_published = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    topic = relationship("Topic", back_populates="lessons")
    resources = relationship("Resource", back_populates="lesson", cascade="all, delete-orphan")


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    resource_type = Column(Enum(ResourceType), default=ResourceType.DOCUMENT, nullable=False)
    url = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    lesson = relationship("Lesson", back_populates="resources")
