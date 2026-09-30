"""CrewAI agents used by the code review crew."""

from __future__ import annotations

import os
from dataclasses import dataclass

from crewai import LLM, Agent

DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"
DEFAULT_MAX_TOKENS = 1024


@dataclass(frozen=True)
class ReviewAgents:
    """The specialist agents that make up the review crew."""

    security: Agent
    optimization: Agent
    documentation: Agent

    def as_list(self) -> list[Agent]:
        """Return the agents in execution order."""
        return [self.security, self.optimization, self.documentation]


def create_llm() -> LLM:
    """Create the Groq-backed LLM shared by all review agents.

    Environment:
        GROQ_API_KEY: Required Groq API key.
        GROQ_MODEL: Optional Groq model id (default ``openai/gpt-oss-120b``).
        GROQ_MAX_TOKENS: Optional response token limit (default 1024).

    Raises:
        ValueError: If required configuration is missing or invalid.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY must be set before creating review agents.")

    model_name = os.getenv("GROQ_MODEL", "").strip() or DEFAULT_GROQ_MODEL
    if not model_name.startswith("groq/"):
        model_name = f"groq/{model_name}"

    raw_max_tokens = os.getenv("GROQ_MAX_TOKENS", "").strip()
    try:
        max_tokens = int(raw_max_tokens) if raw_max_tokens else DEFAULT_MAX_TOKENS
    except ValueError as error:
        raise ValueError("GROQ_MAX_TOKENS must be an integer.") from error
    if max_tokens <= 0:
        raise ValueError("GROQ_MAX_TOKENS must be positive.")

    return LLM(model=model_name, api_key=api_key, temperature=0, max_tokens=max_tokens)


def build_agents(llm: LLM | None = None) -> ReviewAgents:
    """Build the security, optimization, and documentation agents."""
    llm = llm or create_llm()
    common = {"llm": llm, "verbose": False, "allow_delegation": False}

    return ReviewAgents(
        security=Agent(
            role="Application Security Reviewer",
            goal="Identify exploitable security defects in the supplied pull request diff.",
            backstory=(
                "You are a senior application security engineer specializing in OWASP risks, "
                "injection vulnerabilities, authentication, authorization, secrets, and unsafe "
                "data handling."
            ),
            **common,
        ),
        optimization=Agent(
            role="Performance and Code Quality Reviewer",
            goal="Find performance, maintainability, correctness, and PEP 8 issues in the diff.",
            backstory=(
                "You are a senior Python engineer who reasons about time and space complexity, "
                "resource usage, error paths, readability, and idiomatic PEP 8 implementation."
            ),
            **common,
        ),
        documentation=Agent(
            role="Documentation and Review Synthesis Specialist",
            goal="Produce a clear, actionable Markdown review that synthesizes specialist findings.",
            backstory=(
                "You are an exacting technical writer. You distinguish actionable defects from "
                "style preferences, preserve file and line references, and write concise "
                "developer feedback."
            ),
            **common,
        ),
    )
