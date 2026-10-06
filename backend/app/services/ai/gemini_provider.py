import json
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.services.ai.base import AIProvider
from app.services.ai.mock_provider import MockAIProvider

logger = logging.getLogger(__name__)


class GeminiProvider(AIProvider):
    """
    Google Gemini API implementation using REST API.
    Falls back gracefully to MockAIProvider if network or API keys are unavailable.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.AI_API_KEY
        self.model_name = model_name or settings.AI_MODEL_NAME or "gemini-1.5-flash"
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
        self.fallback = MockAIProvider()

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        if not self.api_key or "mock" in self.api_key.lower():
            return self.fallback.generate_text(prompt, system_instruction)

        try:
            payload: Dict[str, Any] = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            if system_instruction:
                payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            with httpx.Client(timeout=20.0) as client:
                res = client.post(
                    f"{self.base_url}?key={self.api_key}",
                    json=payload
                )
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                logger.warning(f"Gemini API returned status {res.status_code}: {res.text}. Using fallback.")
        except Exception as e:
            logger.warning(f"Error calling Gemini API: {e}. Using fallback.")

        return self.fallback.generate_text(prompt, system_instruction)

    def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        system_instruction: str,
        student_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if not self.api_key or "mock" in self.api_key.lower():
            return self.fallback.generate_chat_response(messages, system_instruction, student_context)

        prompt_text = (
            f"You are an encouraging, expert AI Tutor for an AI-Powered Learning System.\n"
            f"Context: {json.dumps(student_context or {})}\n"
            f"Instructions: {system_instruction}\n\n"
            f"Conversation:\n"
        )
        for m in messages:
            prompt_text += f"{m.get('role', 'user').upper()}: {m.get('content')}\n"

        prompt_text += (
            "\nProvide your response in JSON format with keys:\n"
            "\"reply\": (string, your markdown explanation),\n"
            "\"hints\": (list of 2 concise hint strings),\n"
            "\"follow_up_questions\": (list of 2 reflective question strings)\n"
        )

        try:
            raw_text = self.generate_text(prompt_text)
            # Parse json from output
            clean = raw_text.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.endswith("```"):
                clean = clean[:-3]
            parsed = json.loads(clean.strip())
            return {
                "reply": parsed.get("reply", raw_text),
                "hints": parsed.get("hints", []),
                "follow_up_questions": parsed.get("follow_up_questions", [])
            }
        except Exception as e:
            logger.warning(f"Failed parsing Gemini chat response: {e}. Using fallback.")
            return self.fallback.generate_chat_response(messages, system_instruction, student_context)

    def generate_questions(
        self,
        topic_title: str,
        difficulty: str,
        weak_concepts: List[str],
        count: int = 3
    ) -> List[Dict[str, Any]]:
        if not self.api_key or "mock" in self.api_key.lower():
            return self.fallback.generate_questions(topic_title, difficulty, weak_concepts, count)

        prompt = (
            f"Generate {count} multiple choice questions for the topic '{topic_title}' at difficulty '{difficulty}'.\n"
            f"Target these weak concepts: {weak_concepts}.\n"
            f"Return a strict JSON array of objects with keys:\n"
            f"- question_text (string)\n"
            f"- explanation (string)\n"
            f"- difficulty ('{difficulty}')\n"
            f"- question_type ('multiple_choice')\n"
            f"- options_json (array of 4 objects with 'id': 'A'|'B'|'C'|'D' and 'text')\n"
            f"- correct_answer ('A'|'B'|'C'|'D')\n"
            f"- concept_tag (string)\n"
            f"- points (1 for easy, 2 for medium, 3 for hard)\n"
        )
        try:
            raw = self.generate_text(prompt)
            clean = raw.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.endswith("```"):
                clean = clean[:-3]
            parsed = json.loads(clean.strip())
            if isinstance(parsed, list) and len(parsed) > 0:
                for q in parsed:
                    q["is_ai_generated"] = True
                return parsed
        except Exception as e:
            logger.warning(f"Failed parsing Gemini question generation: {e}. Falling back.")

        return self.fallback.generate_questions(topic_title, difficulty, weak_concepts, count)
