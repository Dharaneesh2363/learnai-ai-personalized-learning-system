import json
import logging
from typing import Any, Dict, List, Optional
from app.services.ai.base import AIProvider

logger = logging.getLogger(__name__)


class MockAIProvider(AIProvider):
    """
    Mock AI Provider supplying realistic, pedagogically rich tutoring responses
    and structured assessment questions without requiring external API keys.
    """

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        return f"Mock response for prompt: {prompt[:80]}..."

    def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        system_instruction: str,
        student_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        last_message = messages[-1]["content"] if messages else "Hello"
        student_level = student_context.get("mastery_level", "Developing") if student_context else "Developing"
        topic_title = student_context.get("topic_title", "Python Programming") if student_context else "Python Programming"
        weak_concepts = student_context.get("weak_concepts", []) if student_context else []

        # Personalized tutoring reply
        reply = (
            f"Hello! I am your AI Tutor for **{topic_title}**. "
            f"Based on your profile ({student_level} level), let's break this down step-by-step.\n\n"
        )

        query_lower = last_message.lower()
        if "loop" in query_lower or "for" in query_lower or "while" in query_lower:
            reply += (
                "Remember that loops allow us to repeat code without copying it! "
                "In Python, a `for` loop is typically used when you know how many times you want to iterate "
                "(e.g., iterating over a list or `range(5)`), whereas a `while` loop runs as long as a condition remains `True`.\n\n"
                "```python\n"
                "# Example: Nested loop pattern\n"
                "for row in range(1, 4):\n"
                "    for col in range(1, 4):\n"
                "        print(f'{row}x{col}={row*col}', end=' ')\n"
                "    print()\n"
                "```\n\n"
                "Notice how the inner loop completes all its iterations for every single tick of the outer loop!"
            )
            hints = [
                "Always check your loop termination condition to avoid infinite while loops.",
                "In nested loops, the inner loop runs M times for every 1 step of the outer loop (total N * M steps)."
            ]
            follow_ups = [
                "What would happen if we put a `break` statement inside the inner loop?",
                "Would you like to try a quick 1-question check on loop indices?"
            ]
        elif "function" in query_lower or "def" in query_lower or "return" in query_lower:
            reply += (
                "Functions package reusable units of logic. In Python, you define them with `def`.\n\n"
                "Key distinction:\n"
                "- `print()` simply displays values in the console.\n"
                "- `return` passes a value back to the caller so your program can use it elsewhere.\n\n"
                "```python\n"
                "def calculate_total(price, tax_rate=0.08):\n"
                "    return round(price * (1 + tax_rate), 2)\n\n"
                "total = calculate_total(100) # Returns 108.0\n"
                "```"
            )
            hints = [
                "Variables declared inside a function have local scope and cannot be accessed from outside.",
                "Default arguments must always follow non-default arguments in the parameter list."
            ]
            follow_ups = [
                "Can you explain the difference between parameters and arguments?",
                "What happens if a function executes without an explicit `return` statement?"
            ]
        else:
            reply += (
                f"Regarding your question about **{last_message}**:\n\n"
                "1. **Core Concept**: Break complex logic into smaller sub-problems.\n"
                "2. **State & Control Flow**: Trace variables line-by-line as the interpreter executes them.\n"
                "3. **Practical Tip**: When encountering an unexpected result, print intermediate states.\n\n"
                "How would you approach solving this step with an example?"
            )
            hints = [
                "Try writing pseudo-code on paper before typing the implementation.",
                "Look at the data types of your inputs at each transition."
            ]
            follow_ups = [
                "Would you like to walk through a concrete test case?",
                "Should we review a related practice problem together?"
            ]

        if weak_concepts:
            reply += f"\n\n*(Note: I noticed you've recently had questions around **{', '.join(weak_concepts)}**, so feel free to ask me to clarify those specific areas anytime!)*"

        return {
            "reply": reply,
            "hints": hints,
            "follow_up_questions": follow_ups
        }

    def generate_questions(
        self,
        topic_title: str,
        difficulty: str,
        weak_concepts: List[str],
        count: int = 3
    ) -> List[Dict[str, Any]]:
        """Generates realistic curriculum questions based on topic and difficulty."""
        diff_str = difficulty.lower()
        questions = []
        for i in range(1, count + 1):
            questions.append({
                "question_text": f"[{diff_str.upper()}] In the context of {topic_title}, what is the expected output or behavior when handling scenario #{i}?",
                "explanation": f"Scenario #{i} demonstrates fundamental mechanics in {topic_title} at {diff_str} difficulty.",
                "difficulty": diff_str,
                "question_type": "multiple_choice",
                "options_json": [
                    {"id": "A", "text": f"Option A: Correct deterministic execution for {topic_title}"},
                    {"id": "B", "text": f"Option B: Raises an unexpected TypeError or IndexError"},
                    {"id": "C", "text": f"Option C: Skips execution and terminates silently"},
                    {"id": "D", "text": f"Option D: Results in an infinite loop or resource exhaustion"},
                ],
                "correct_answer": "A",
                "concept_tag": weak_concepts[0] if weak_concepts else "fundamentals",
                "points": 3 if diff_str == "hard" else (2 if diff_str == "medium" else 1),
                "is_ai_generated": True
            })
        return questions
