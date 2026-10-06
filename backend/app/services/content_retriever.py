import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session, joinedload

from app.models.course import Course, Lesson, Module, Topic, TopicPrerequisite

logger = logging.getLogger(__name__)


class LearningContextRetriever:
    """
    RAG-Ready Content Retrieval Architecture.
    
    Provides grounded pedagogical context to the AI Tutor and AI Question Generator.
    Extracts relevant lesson text, topic syllabi, and prerequisite concept summaries.
    
    Architecture Note for Production/Interview:
    This service defines the exact semantic contract for Retrieval-Augmented Generation (RAG).
    In this modular monolith stage, it performs structured lexical retrieval over relational lesson markdown.
    When scaling to vector search (e.g. pgvector, Pinecone, or Vertex AI Search), the
    `retrieve_context_for_topic` and `retrieve_context_for_query` methods seamlessly swap their internal
    lookups from SQL filters to cosine similarity over embedding vectors without breaking callers.
    """

    @classmethod
    def retrieve_context_for_topic(
        cls,
        db: Session,
        topic_id: int,
        max_lessons: int = 3,
        include_prerequisites: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieves grounded curriculum context for a given topic:
        - Topic metadata, description, and parent module/course
        - Core lesson snippets and code samples
        - Prerequisite concept summaries
        """
        topic = (
            db.query(Topic)
            .options(joinedload(Topic.module).joinedload(Module.course))
            .filter(Topic.id == topic_id)
            .first()
        )
        if not topic:
            return {"topic_title": "Unknown Topic", "content_snippets": [], "prerequisites": []}

        course_title = topic.module.course.title if topic.module and topic.module.course else "General"
        module_title = topic.module.title if topic.module else "General"

        # Retrieve published lessons for this topic
        lessons = (
            db.query(Lesson)
            .filter(Lesson.topic_id == topic_id, Lesson.is_published == True)
            .order_by(Lesson.order_index)
            .limit(max_lessons)
            .all()
        )

        snippets = []
        for l in lessons:
            # Clean snippet (truncate to 800 chars per lesson to fit prompt budget)
            clean_content = l.content_markdown.strip()
            summary = clean_content[:800] + ("..." if len(clean_content) > 800 else "")
            snippets.append({
                "lesson_id": l.id,
                "lesson_title": l.title,
                "snippet": summary,
                "duration_minutes": l.duration_minutes
            })

        # Retrieve prerequisite topic summaries if requested
        prereq_summaries = []
        if include_prerequisites:
            prereqs = (
                db.query(TopicPrerequisite)
                .filter(TopicPrerequisite.topic_id == topic_id)
                .all()
            )
            for p in prereqs:
                p_topic = db.query(Topic).filter(Topic.id == p.prerequisite_topic_id).first()
                if p_topic:
                    prereq_summaries.append({
                        "prerequisite_id": p_topic.id,
                        "title": p_topic.title,
                        "description": p_topic.description or ""
                    })

        return {
            "topic_id": topic.id,
            "topic_title": topic.title,
            "topic_description": topic.description or "",
            "course_title": course_title,
            "module_title": module_title,
            "snippets": snippets,
            "prerequisites": prereq_summaries,
            "grounding_text": cls._format_grounding_text(topic.title, snippets, prereq_summaries)
        }

    @classmethod
    def retrieve_context_for_query(
        cls,
        db: Session,
        query: str,
        topic_id: Optional[int] = None,
        limit: int = 2
    ) -> str:
        """
        Retrieves relevant lesson excerpts matching a student question or query keywords.
        Prepares grounded context for RAG prompts.
        """
        lesson_query = db.query(Lesson).filter(Lesson.is_published == True)
        if topic_id:
            lesson_query = lesson_query.filter(Lesson.topic_id == topic_id)

        all_lessons = lesson_query.all()
        if not all_lessons:
            return ""

        # Lexical keyword matching over lesson title and content
        keywords = [w.lower() for w in query.split() if len(w) > 3]
        scored_lessons = []

        for l in all_lessons:
            text = (l.title + " " + l.content_markdown).lower()
            score = sum(text.count(kw) for kw in keywords)
            if score > 0 or not keywords:
                scored_lessons.append((score, l))

        scored_lessons.sort(key=lambda x: x[0], reverse=True)
        top_matches = [l for _, l in scored_lessons[:limit]] if scored_lessons else all_lessons[:limit]

        grounding_parts = []
        for l in top_matches:
            grounding_parts.append(
                f"### Lesson: {l.title}\n{l.content_markdown[:600]}..."
            )

        return "\n\n".join(grounding_parts)

    @staticmethod
    def _format_grounding_text(
        topic_title: str,
        snippets: List[Dict[str, Any]],
        prerequisites: List[Dict[str, Any]]
    ) -> str:
        """Formats structured snippets into a clean markdown grounding section."""
        lines = [f"## Course Context for '{topic_title}':"]
        if prerequisites:
            lines.append("Prerequisites: " + ", ".join(p["title"] for p in prerequisites))
        for s in snippets:
            lines.append(f"\n[Source: {s['lesson_title']}]\n{s['snippet']}")
        return "\n".join(lines)
