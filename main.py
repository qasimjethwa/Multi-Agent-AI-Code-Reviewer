"""Command-line entry point for the multi-agent GitHub pull request reviewer."""

from __future__ import annotations

# CrewAI + Groq workaround:
# CrewAI can inject `cache_breakpoint` into messages sent to
# non-Anthropic providers such as Groq. Groq rejects this field.
import crewai.llms.cache as _crewai_cache

_crewai_cache.mark_cache_breakpoint = lambda msg: msg

import argparse
import logging
import os
import sys

from crewai import Crew, Process
from dotenv import load_dotenv

from github_utils import (
    authenticate_github,
    fetch_pull_request_diff,
    post_pull_request_comment,
)

LOGGER = logging.getLogger(__name__)

DEFAULT_MAX_DIFF_CHARS = 6000
TRUNCATION_MARKER = "\n...[diff truncated]...\n"
REVIEW_HEADER = "## 🤖 AI Code Review\n\n"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Review a GitHub pull request with specialized CrewAI agents."
    )
    parser.add_argument(
        "repository",
        help="GitHub repository in the form owner/repository",
    )
    parser.add_argument(
        "pull_request",
        type=int,
        help="Pull request number",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the review instead of posting it as a PR comment.",
    )
    return parser.parse_args(argv)


def truncate_diff(
    diff: str,
    max_chars: int = DEFAULT_MAX_DIFF_CHARS,
) -> str:
    """Bound the diff size sent to the LLM, keeping its head and tail."""
    if max_chars <= 0:
        raise ValueError("max_chars must be positive.")

    if len(diff) <= max_chars:
        return diff

    half = max_chars // 2

    return (
        diff[:half]
        + TRUNCATION_MARKER
        + diff[-(max_chars - half):]
    )


def _max_diff_chars() -> int:
    """Read and validate MAX_DIFF_CHARS from the environment."""
    raw = os.getenv("MAX_DIFF_CHARS", "").strip()

    if not raw:
        return DEFAULT_MAX_DIFF_CHARS

    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError(
            "MAX_DIFF_CHARS must be an integer."
        ) from error

    if value <= 0:
        raise ValueError("MAX_DIFF_CHARS must be positive.")

    return value


def build_crew() -> Crew:
    """Build the sequential review crew."""
    from agents import build_agents
    from tasks import build_tasks

    agents = build_agents()

    return Crew(
        agents=agents.as_list(),
        tasks=build_tasks(agents),
        process=Process.sequential,
        verbose=False,
    )


def run_review(code_diff: str) -> str:
    """Run the crew over a diff and return the Markdown review."""
    crew = build_crew()

    result = crew.kickoff(
        inputs={"code_diff": code_diff}
    )

    review_markdown = str(
        getattr(result, "raw", result) or ""
    ).strip()

    if not review_markdown:
        raise RuntimeError("CrewAI returned an empty review.")

    return review_markdown


def main(argv: list[str] | None = None) -> int:
    """Fetch, review, and publish a pull request review."""
    load_dotenv()

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    args = _parse_args(argv)

    github = None

    try:
        LOGGER.info(
            "Starting review for %s#%s.",
            args.repository,
            args.pull_request,
        )

        github = authenticate_github(
            os.getenv("GITHUB_TOKEN", "")
        )

        code_diff = fetch_pull_request_diff(
            github,
            args.repository,
            args.pull_request,
        )

        review_diff = truncate_diff(
            code_diff,
            _max_diff_chars(),
        )

        LOGGER.info("Running CrewAI review tasks.")

        review_markdown = (
            REVIEW_HEADER
            + run_review(review_diff)
        )

        if args.dry_run:
            print(review_markdown)
            return 0

        comment_url = post_pull_request_comment(
            github,
            args.repository,
            args.pull_request,
            review_markdown,
        )

        LOGGER.info(
            "Review published: %s",
            comment_url,
        )

        return 0

    except Exception:
        LOGGER.exception(
            "Pull request review failed."
        )
        return 1

    finally:
        if github is not None:
            github.close()


if __name__ == "__main__":
    sys.exit(main())