"""CrewAI agents used by the code review crew."""

from __future__ import annotations

import os

from crewai import Agent
from langchain_groq import ChatGroq


def _create_llm() -> ChatGroq:
    """Create the configured Groq chat model for all review agents.

    Returns:
        A ChatGroq client configured with the default review model.

    Raises:
        ValueError: If ``GROQ_API_KEY`` is not configured.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY must be set before creating review agents.")

    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
    if not model_name:
        raise ValueError("GROQ_MODEL must not be empty.")

    return ChatGroq(
        model=model_name,
        groq_api_key=api_key,
        temperature=0,
    )


_llm = _create_llm()

security_agent = Agent(
    role="Application Security Reviewer",
    goal="Identify exploitable security defects in the supplied pull request diff.",
    backstory=(
        "You are a senior application security engineer specializing in OWASP risks, "
        "injection vulnerabilities, authentication, authorization, secrets, and unsafe data handling."
    ),
    llm=_llm,
    verbose=False,
    allow_delegation=False,
)

optimization_agent = Agent(
    role="Performance and Code Quality Reviewer",
    goal="Find performance, maintainability, correctness, and PEP 8 issues in the diff.",
    backstory=(
        "You are a senior Python engineer who reasons about time and space complexity, "
        "resource usage, error paths, readability, and idiomatic PEP 8 implementation."
    ),
    llm=_llm,
    verbose=False,
    allow_delegation=False,
)

documentation_agent = Agent(
    role="Documentation and Review Synthesis Specialist",
    goal="Produce a clear, actionable Markdown review that synthesizes specialist findings.",
    backstory=(
        "You are an exacting technical writer. You distinguish actionable defects from "
        "style preferences, preserve file and line references, and write concise developer feedback."
    ),
    llm=_llm,
    verbose=False,
    allow_delegation=False,
)