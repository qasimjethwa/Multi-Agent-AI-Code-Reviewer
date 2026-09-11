"""GitHub API helpers for retrieving pull request diffs and posting reviews."""

from __future__ import annotations

import logging

from github import Auth, Github
from github.GithubException import BadCredentialsException, GithubException
from github.PullRequest import PullRequest

LOGGER = logging.getLogger(__name__)


def authenticate_github(token: str) -> Github:
    """Authenticate with GitHub and verify that the token is usable.

    Args:
        token: GitHub personal access token or fine-grained access token.

    Returns:
        An authenticated PyGithub client.

    Raises:
        ValueError: If the token is empty.
        BadCredentialsException: If GitHub rejects the credentials.
        GithubException: If GitHub returns another authentication failure.
    """
    if not token or not token.strip():
        raise ValueError("GITHUB_TOKEN must not be empty.")

    github = Github(auth=Auth.Token(token.strip()))
    try:
        github.get_user().login
    except BadCredentialsException:
        LOGGER.exception("GitHub authentication failed: invalid credentials.")
        github.close()
        raise
    except GithubException:
        LOGGER.exception("GitHub authentication failed during token verification.")
        github.close()
        raise

    LOGGER.info("Authenticated with GitHub.")
    return github


def fetch_pull_request_diff(
    github: Github,
    repository_name: str,
    pull_request_number: int,
) -> str:
    """Fetch the reviewable unified diff for a pull request.

    PyGithub exposes changed files and their patch text rather than a direct
    text-diff convenience method. This function reconstructs the diff while
    retaining file-level metadata for binary or unusually large files whose
    patch field is omitted by GitHub.

    Args:
        github: Authenticated PyGithub client.
        repository_name: Full repository name, such as ``owner/repository``.
        pull_request_number: Positive pull request number.

    Returns:
        A raw string containing the pull request's file patches.

    Raises:
        ValueError: If the repository name or PR number is invalid.
        GithubException: If GitHub cannot return the pull request or files.
    """
    if not repository_name or "/" not in repository_name:
        raise ValueError("repository_name must use the 'owner/repository' format.")
    if pull_request_number <= 0:
        raise ValueError("pull_request_number must be positive.")

    try:
        pull_request: PullRequest = github.get_repo(repository_name).get_pull(
            pull_request_number
        )
        diff_parts: list[str] = []
        for changed_file in pull_request.get_files():
            patch = changed_file.patch
            if patch:
                diff_parts.append(
                    f"diff --git a/{changed_file.filename} b/{changed_file.filename}\n"
                    f"# status: {changed_file.status}, additions: {changed_file.additions}, "
                    f"deletions: {changed_file.deletions}\n{patch}"
                )
            else:
                diff_parts.append(
                    f"diff --git a/{changed_file.filename} b/{changed_file.filename}\n"
                    f"# status: {changed_file.status}, additions: {changed_file.additions}, "
                    f"deletions: {changed_file.deletions}\n"
                    "# Patch unavailable (binary or GitHub size limit)."
                )

        if not diff_parts:
            raise GithubException(422, "The pull request contains no changed files.")

        diff = "\n\n".join(diff_parts)
        LOGGER.info(
            "Fetched diff for %s#%s (%d files, %d characters).",
            repository_name,
            pull_request_number,
            len(diff_parts),
            len(diff),
        )
        return diff
    except GithubException as error:
        if error.status == 401:
            LOGGER.exception("GitHub authentication failed while fetching the diff.")
        elif error.status in (403, 429):
            LOGGER.exception("GitHub API rate limit or permission failure while fetching the diff.")
        else:
            LOGGER.exception(
                "GitHub API error while fetching %s#%s.",
                repository_name,
                pull_request_number,
            )
        raise


def post_pull_request_comment(
    github: Github,
    repository_name: str,
    pull_request_number: int,
    comment: str,
) -> str:
    """Post a Markdown comment on a pull request.

    Args:
        github: Authenticated PyGithub client.
        repository_name: Full repository name, such as ``owner/repository``.
        pull_request_number: Positive pull request number.
        comment: Markdown content to publish.

    Returns:
        The URL of the created issue comment.

    Raises:
        ValueError: If inputs are invalid.
        GithubException: If GitHub rejects the comment or request.
    """
    if not repository_name or "/" not in repository_name:
        raise ValueError("repository_name must use the 'owner/repository' format.")
    if pull_request_number <= 0:
        raise ValueError("pull_request_number must be positive.")
    if not comment or not comment.strip():
        raise ValueError("comment must not be empty.")

    try:
        pull_request = github.get_repo(repository_name).get_pull(pull_request_number)
        issue_comment = pull_request.create_issue_comment(comment.strip())
        LOGGER.info(
            "Posted review comment to %s#%s.", repository_name, pull_request_number
        )
        return issue_comment.html_url
    except GithubException as error:
        if error.status == 401:
            LOGGER.exception("GitHub authentication failed while posting the review.")
        elif error.status in (403, 429):
            LOGGER.exception("GitHub API rate limit or permission failure while posting the review.")
        else:
            LOGGER.exception(
                "GitHub API error while posting to %s#%s.",
                repository_name,
                pull_request_number,
            )
        raise