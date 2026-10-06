from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db, require_role
from app.models.course import Course, Module, Topic, Lesson, Resource, TopicPrerequisite
from app.models.user import User, UserRole
from app.schemas.course import (
    CourseResponse,
    CourseDetailResponse,
    CourseCreate,
    CourseUpdate,
    ModuleResponse,
    ModuleBase,
    ModuleCreate,
    TopicResponse,
    TopicCreate,
    TopicUpdate,
    LessonResponse,
    LessonCreate,
    LessonUpdate,
    TopicPrerequisiteResponse,
)

router = APIRouter(prefix="/courses", tags=["Courses & Learning Content"])


@router.get("", response_model=List[CourseResponse])
def get_courses(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Any:
    """List all available published courses."""
    query = db.query(Course).filter(Course.is_published == True)
    if category:
        query = query.filter(Course.category.ilike(f"%{category}%"))
    return query.all()


@router.get("/{course_id}", response_model=CourseDetailResponse)
def get_course_detail(
    course_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve full course structure including modules, topics, and lessons."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Eagerly load nested modules and topics
    modules = (
        db.query(Module)
        .filter(Module.course_id == course_id)
        .order_by(Module.order_index)
        .all()
    )

    module_responses = []
    for mod in modules:
        topics = (
            db.query(Topic)
            .filter(Topic.module_id == mod.id)
            .order_by(Topic.order_index)
            .all()
        )
        
        topic_responses = []
        for top in topics:
            lessons = (
                db.query(Lesson)
                .filter(Lesson.topic_id == top.id, Lesson.is_published == True)
                .order_by(Lesson.order_index)
                .all()
            )
            prereqs = (
                db.query(TopicPrerequisite)
                .filter(TopicPrerequisite.topic_id == top.id)
                .all()
            )
            prereq_resps = []
            for p in prereqs:
                prereq_topic = db.query(Topic).filter(Topic.id == p.prerequisite_topic_id).first()
                prereq_resps.append(
                    TopicPrerequisiteResponse(
                        prerequisite_topic_id=p.prerequisite_topic_id,
                        prerequisite_title=prereq_topic.title if prereq_topic else None
                    )
                )

            topic_responses.append(
                TopicResponse(
                    id=top.id,
                    module_id=top.module_id,
                    title=top.title,
                    slug=top.slug,
                    description=top.description,
                    order_index=top.order_index,
                    estimated_minutes=top.estimated_minutes,
                    created_at=top.created_at,
                    updated_at=top.updated_at,
                    lessons=[LessonResponse.model_validate(l) for l in lessons],
                    prerequisites=prereq_resps
                )
            )

        module_responses.append(
            ModuleResponse(
                id=mod.id,
                course_id=mod.course_id,
                title=mod.title,
                description=mod.description,
                order_index=mod.order_index,
                created_at=mod.created_at,
                updated_at=mod.updated_at,
                topics=topic_responses
            )
        )

    res = CourseDetailResponse(
        id=course.id,
        title=course.title,
        slug=course.slug,
        description=course.description,
        category=course.category,
        difficulty=course.difficulty,
        thumbnail_url=course.thumbnail_url,
        is_published=course.is_published,
        created_at=course.created_at,
        updated_at=course.updated_at,
        modules=module_responses
    )
    return res


@router.get("/topics/{topic_id}", response_model=TopicResponse)
def get_topic_detail(
    topic_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve detailed information for a specific topic."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    lessons = (
        db.query(Lesson)
        .filter(Lesson.topic_id == topic.id, Lesson.is_published == True)
        .order_by(Lesson.order_index)
        .all()
    )
    prereqs = (
        db.query(TopicPrerequisite)
        .filter(TopicPrerequisite.topic_id == topic.id)
        .all()
    )
    prereq_resps = []
    for p in prereqs:
        prereq_topic = db.query(Topic).filter(Topic.id == p.prerequisite_topic_id).first()
        prereq_resps.append(
            TopicPrerequisiteResponse(
                prerequisite_topic_id=p.prerequisite_topic_id,
                prerequisite_title=prereq_topic.title if prereq_topic else None
            )
        )

    return TopicResponse(
        id=topic.id,
        module_id=topic.module_id,
        title=topic.title,
        slug=topic.slug,
        description=topic.description,
        order_index=topic.order_index,
        estimated_minutes=topic.estimated_minutes,
        created_at=topic.created_at,
        updated_at=topic.updated_at,
        lessons=[LessonResponse.model_validate(l) for l in lessons],
        prerequisites=prereq_resps
    )


@router.get("/lessons/{lesson_id}", response_model=LessonResponse)
def get_lesson_detail(
    lesson_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve complete content and resources for a specific lesson."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


# Teacher / Admin Management routes
@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    req: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TEACHER, UserRole.ADMIN))
) -> Any:
    """Create a new course (Teacher or Admin only)."""
    existing = db.query(Course).filter(Course.slug == req.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="A course with this slug already exists")
    course = Course(**req.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.post("/{course_id}/modules", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED)
def create_module(
    course_id: int,
    req: ModuleBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TEACHER, UserRole.ADMIN))
) -> Any:
    """Create a new module within a course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    module = Module(course_id=course_id, **req.model_dump())
    db.add(module)
    db.commit()
    db.refresh(module)
    return module
