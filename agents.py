"""CrewAI agents configured for the AI Code Reviewer pipeline."""

import os
from crewai import Agent, LLM

# Initialize Groq LLM using CrewAI's native LLM class
llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    temperature=0.1,
    api_key=os.getenv("GROQ_API_KEY"),
)

# 1. Security Specialist Agent
security_agent = Agent(
    role="Senior Cybersecurity & Vulnerability Auditor",
    goal=(
        "Scan provided code diffs for security vulnerabilities, hardcoded secrets, "
        "injection risks, and OWASP Top 10 compliance issues."
    ),
    backstory=(
        "You are an elite application security auditor with extensive experience "
        "detecting operational vulnerabilities, credential leaks, and flawed authorization "
        "logic in repository pull requests."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm,
)

# 2. Performance & Optimization Agent
optimization_agent = Agent(
    role="Principal Software Optimization Engineer",
    goal=(
        "Analyze code diffs for time and space complexity ($O(n)$ bounds), performance bottlenecks, "
        "edge case handling, and adherence to clean code standards."
    ),
    backstory=(
        "You are a systems performance architect specializing in algorithmic refactoring, "
        "minimizing unnecessary compute and memory usage, and ensuring code follows PEP 8 guidelines."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm,
)

# 3. Documentation & Quality Agent
documentation_agent = Agent(
    role="Lead Technical Writer & Code Quality Specialist",
    goal=(
        "Evaluate code diffs for docstring completeness, type annotation coverage, "
        "readability, and draft structured summary notes for developers."
    ),
    backstory=(
        "You are a technical documentation lead ensuring repositories remain well-typed, "
        "thoroughly documented, and easy for new maintainers to navigate."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm,
)