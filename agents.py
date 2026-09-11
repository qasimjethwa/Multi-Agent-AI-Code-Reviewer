"""CrewAI agents used by the multi-agent pull request reviewer."""

from __future__ import annotations

import os

from crewai import Agent, LLM


def _create_llm() -> LLM:
    """
    Create the shared CrewAI LLM configuration.

    CrewAI delegates Groq models through LiteLLM, so the model must use
    the `groq/` provider prefix.

    Environment variables:
        GROQ_API_KEY:
            Groq API key.
        REVIEW_MODEL:
            Groq model identifier. Defaults to a currently supported model.

    Returns:
        Configured CrewAI LLM instance.

    Raises:
        ValueError:
            If GROQ_API_KEY is missing.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY must be set before creating review agents."
        )

    model = os.getenv(
        "REVIEW_MODEL",
        "groq/openai/gpt-oss-120b",
    ).strip()

    if not model:
        raise ValueError("REVIEW_MODEL cannot be empty.")

    return LLM(
        model=model,
        api_key=api_key,
        temperature=0,
        max_tokens=8192,
    )


llm = _create_llm()


security_agent = Agent(
    role="Application Security Reviewer",
    goal=(
        "Identify exploitable security defects in the supplied pull request diff "
        "and recommend concrete remediations."
    ),
    backstory=(
        "You are a senior application security engineer specializing in OWASP "
        "vulnerabilities, injection attacks, authentication, authorization, "
        "secrets exposure, unsafe deserialization, SSRF, path traversal, and "
        "unsafe handling of untrusted input."
    ),
    llm=llm,
    verbose=False,
    allow_delegation=False,
)


optimization_agent = Agent(
    role="Performance and Code Quality Reviewer",
    goal=(
        "Find performance, correctness, maintainability, resource-management, "
        "and Python code-quality problems in the supplied pull request diff."
    ),
    backstory=(
        "You are a senior Python engineer with strong knowledge of algorithmic "
        "complexity, memory usage, I/O performance, error handling, maintainability, "
        "idiomatic Python, and PEP 8."
    ),
    llm=llm,
    verbose=False,
    allow_delegation=False,
)


documentation_agent = Agent(
    role="Documentation and Review Synthesis Specialist",
    goal=(
        "Produce a concise, actionable Markdown pull request review by synthesizing "
        "the specialist findings and identifying documentation or clarity issues."
    ),
    backstory=(
        "You are an exacting technical writer and senior engineer. You separate "
        "real defects from subjective style preferences, preserve file and line "
        "references, eliminate duplicate findings, and produce practical developer "
        "feedback."
    ),
    llm=llm,
    verbose=False,
    allow_delegation=False,
)