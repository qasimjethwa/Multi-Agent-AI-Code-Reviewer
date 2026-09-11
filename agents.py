import os
from crewai import Agent, LLM

# Configure Groq LLM using CrewAI's LLM class
llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    temperature=0.1,
    api_key=os.getenv("GROQ_API_KEY")
)

# Example agent definition using the updated LLM configuration
security_agent = Agent(
    role="Security Specialist",
    goal="Scan code diffs for security vulnerabilities and compliance issues",
    backstory="An expert cybersecurity auditor focused on identifying security risks.",
    verbose=True,
    allow_delegation=False,
    llm=llm
)