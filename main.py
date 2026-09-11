"""Command-line entry point for the multi-agent GitHub pull request reviewer."""

from __future__ import annotations

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


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed repository name and pull request number.
    """
    parser = argparse.ArgumentParser(
        description="Review a GitHub pull request with specialized CrewAI agents."
    )
    parser.add_argument("repository", help="GitHub repository in the form owner/repository")
    parser.add_argument("pull_request", type=int, help="Pull request number")
    return parser.parse_args()


def _build_crew() -> Crew:
    """Build the synchronous review crew.

    Returns:
        A CrewAI crew containing the specialist and synthesis tasks.
    """
    from agents import documentation_agent, optimization_agent, security_agent
    from tasks import documentation_task, optimization_task, security_task

    return Crew(
        agents=[security_agent, optimization_agent, documentation_agent],
        tasks=[security_task, optimization_task, documentation_task],
        process=Process.sequential,
        verbose=False,
    )


def main() -> int:
    """Fetch, review, synthesize, and publish a pull request review.

    Returns:
        Zero on success and one on an expected configuration or runtime failure.
    """
    load_dotenv()
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = _parse_args()
    token = os.getenv("GITHUB_TOKEN", "")

    github = None
    try:
        LOGGER.info("Starting review for %s#%s.", args.repository, args.pull_request)
        github = authenticate_github(token)
        code_diff = fetch_pull_request_diff(github, args.repository, args.pull_request)

        crew = _build_crew()
        LOGGER.info("Running CrewAI review tasks.")
        result = crew.kickoff(inputs={"code_diff": code_diff})
        review_markdown = str(result).strip()
        if not review_markdown:
            raise RuntimeError("CrewAI returned an empty review.")

        comment_url = post_pull_request_comment(
            github,
            args.repository,
            args.pull_request,
            review_markdown,
        )
        LOGGER.info("Review published: %s", comment_url)
        return 0
    except Exception:
        LOGGER.exception("Pull request review failed.")
        return 1
    finally:
        if github is not None:
            github.close()


if __name__ == "__main__":
    sys.exit(main())