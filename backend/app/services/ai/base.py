from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class AIProvider(ABC):
    """Abstract base class for decoupled AI providers."""

    @abstractmethod
    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generate a raw text response given a prompt and optional system instruction."""
        pass

    @abstractmethod
    def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        system_instruction: str,
        student_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate contextual AI Tutor response.
        Returns:
            {
                "reply": str,
                "hints": List[str],
                "follow_up_questions": List[str]
            }
        """
        pass

    @abstractmethod
    def generate_questions(
        self,
        topic_title: str,
        difficulty: str,
        weak_concepts: List[str],
        count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate structured multiple-choice quiz questions.
        Returns list of question dicts matching Question schema.
        """
        pass
