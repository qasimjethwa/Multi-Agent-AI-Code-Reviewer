"""CrewAI tasks for specialist analysis and final review synthesis."""

from __future__ import annotations

from crewai import Task

from agents import documentation_agent, optimization_agent, security_agent


security_task = Task(
    description=(
        "Review the following pull request diff for security issues:\n\n"
        "{code_diff}\n\n"
        "Focus on OWASP vulnerabilities, injection risks, authentication and authorization, "
        "secrets exposure, unsafe deserialization, and insecure handling of untrusted input. "
        "Only report findings supported by the diff. Include affected file and line context "
        "when available, explain impact, and suggest a concrete remediation. Return Markdown-formatted output."
    ),
    expected_output="Markdown security findings with severity, evidence, impact, and remediation.",
    agent=security_agent,
)

optimization_task = Task(
    description=(
        "Review the following pull request diff for performance and code quality issues:\n\n"
        "{code_diff}\n\n"
        "Analyze time and space complexity, unnecessary I/O or allocations, resource handling, "
        "correctness risks, maintainability, and PEP 8 compliance. Only report actionable findings "
        "supported by the diff. Include affected file and line context when available and propose "
        "a concrete improvement. Return Markdown-formatted output."
    ),
    expected_output="Markdown performance and quality findings with evidence and recommended fixes.",
    agent=optimization_agent,
)

documentation_task = Task(
    description=(
        "Synthesize the security and optimization reviews below into the final pull request review. "
        "Also assess the changed code's clarity, docstrings, naming, and documentation needs.\n\n"
        "Original diff:\n{code_diff}\n\n"
        "Create a concise Markdown review with: an overall summary, prioritized actionable findings, "
        "file/line references where available, and a short documentation/clarity section. Do not invent "
        "issues, repeat duplicate findings, or include hidden reasoning. If no actionable findings exist, "
        "say so and summarize what was reviewed. Return only Markdown-formatted output."
    ),
    expected_output="A synthesized Markdown pull request review suitable for posting as a GitHub comment.",
    agent=documentation_agent,
    context=[security_task, optimization_task],
)