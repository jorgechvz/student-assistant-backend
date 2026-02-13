"""Prompt builder module."""

from functools import lru_cache
from pathlib import Path
from typing import Optional


class PromptBuilder:
    """Service for managing Loop prompts"""

    def __init__(self, prompt_dir: Optional[Path] = None) -> None:
        if prompt_dir is None:
            self._prompt_dir = Path(__file__).parent / "templates"
        else:
            self._prompt_dir = prompt_dir

    @lru_cache(maxsize=1)
    def _load_system_prompt_template(self, filename: str = "") -> str:
        """
        Load the system prompt template from a file.
        """
        prompt_file = self._prompt_dir / filename

        try:
            with open(prompt_file, "r", encoding="utf-8") as file:
                return file.read().strip()
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"System prompt template not found: {prompt_file}"
            ) from exc

    def system_assessment_prompt(
        self,
        *,
        template_name: str = "system_assessment_prompt_v2.txt",
    ) -> str:
        """
        Generate the prompt for the assessment system message.
        """

        return self._load_system_prompt_template(template_name)

    def user_assessment_prompt(
        self,
        *,
        examples: str,
        learner_response: str,
        template_name: str = "user_assessment_prompt_v1.txt",
    ) -> str:
        """
        Generate the prompt for the assessment user message.
        """
        template = self._load_system_prompt_template(template_name)
        return template.format(
            examples=examples,
            learner_response=learner_response,
        )

    def student_assistant_system_prompt(
        self,
        has_integrations: bool = True,
    ) -> str:
        """
        Get the system prompt for the student assistant chatbot.

        Args:
            has_integrations: Whether the user has any integrations connected

        Returns:
            System prompt string
        """
        if has_integrations:
            return self._load_system_prompt_template("student_assistant_system.txt")
        else:
            return self._load_system_prompt_template("no_integrations_system.txt")

    def guardrails_prompt(self) -> str:
        """
        Get the guardrails prompt for handling out-of-scope requests.

        Returns:
            Guardrails prompt string
        """
        return self._load_system_prompt_template("guardrails.txt")
