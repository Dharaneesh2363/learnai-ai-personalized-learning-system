import json
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.services.ai.base import AIProvider
from app.services.ai.mock_provider import MockAIProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """
    OpenAI API implementation using REST endpoint.
    Falls back gracefully to MockAIProvider if network or API keys are unavailable.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.AI_API_KEY
        self.model_name = model_name or "gpt-4o-mini"
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.fallback = MockAIProvider()

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        if not self.api_key or "mock" in self.api_key.lower():
            return self.fallback.generate_text(prompt, system_instruction)

        try:
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.4
            }

            with httpx.Client(timeout=20.0) as client:
                res = client.post(self.base_url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"]
                logger.warning(f"OpenAI API status {res.status_code}: {res.text}. Falling back.")
        except Exception as e:
            logger.warning(f"OpenAI error: {e}. Falling back.")

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
            f"You are an encouraging, expert AI Tutor for LearnAI.\n"
            f"Student Context: {json.dumps(student_context or {})}\n"
            f"Instructions: {system_instruction}\n\n"
            f"Provide your response in JSON format with keys:\n"
            "\"reply\": (string, your markdown explanation),\n"
            "\"hints\": (list of 2 concise hint strings),\n"
            "\"follow_up_questions\": (list of 2 reflective question strings)\n\n"
            "Conversation History:\n"
        )
        for m in messages:
            prompt_text += f"{m.get('role', 'user').upper()}: {m.get('content')}\n"

        try:
            raw_text = self.generate_text(prompt_text, system_instruction)
            clean = raw_text.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.endswith("```"):
                clean = clean[:-3]
            parsed = json.loads(clean.strip())
            return {
                "reply": parsed.get("reply", raw_text),
                "hints": parsed.get("hints", ["Review fundamental syntax", "Trace execution with sample input"]),
                "follow_up_questions": parsed.get("follow_up_questions", ["Would you like to see another example?"])
            }
        except Exception as e:
            logger.warning(f"OpenAI chat JSON parsing error: {e}. Falling back.")
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
            f"Generate {count} multiple choice questions for topic '{topic_title}' at difficulty '{difficulty}'.\n"
            f"Target student weak concepts if applicable: {', '.join(weak_concepts)}.\n\n"
            f"Output strictly valid JSON array of objects with keys:\n"
            f"- question_text (string)\n"
            f"- explanation (string)\n"
            f"- difficulty ('easy', 'medium', or 'hard')\n"
            f"- options_json (array of 4 objects: [{{\"id\": \"A\", \"text\": \"...\"}}, ...])\n"
            f"- correct_answer (single letter 'A', 'B', 'C', or 'D')\n"
            f"- concept_tag (string)\n"
            f"- points (integer, 1 for easy, 2 for medium, 3 for hard)\n"
        )

        try:
            raw_text = self.generate_text(prompt, "You are a curriculum designer generating assessment questions.")
            clean = raw_text.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.endswith("```"):
                clean = clean[:-3]
            parsed = json.loads(clean.strip())
            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed
        except Exception as e:
            logger.warning(f"OpenAI questions JSON parsing error: {e}. Falling back.")

        return self.fallback.generate_questions(topic_title, difficulty, weak_concepts, count)
