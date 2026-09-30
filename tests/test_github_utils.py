from unittest.mock import MagicMock

import pytest
from github.GithubException import GithubException

import github_utils


def _file(name, patch="@@ -1 +1 @@\n-a\n+b", status="modified"):
    f = MagicMock()
    f.filename, f.patch, f.status, f.additions, f.deletions = name, patch, status, 1, 1
    return f


def _client(files):
    client = MagicMock()
    client.get_repo.return_value.get_pull.return_value.get_files.return_value = files
    return client


def test_authenticate_rejects_empty_token():
    with pytest.raises(ValueError):
        github_utils.authenticate_github("   ")


def test_authenticate_returns_client():
    client = github_utils.authenticate_github("abc")
    assert client is not None
    client.close()


def test_fetch_diff_includes_patches_and_binary_placeholder():
    diff = github_utils.fetch_pull_request_diff(
        _client([_file("a.py"), _file("img.png", patch=None)]), "o/r", 1
    )
    assert "diff --git a/a.py b/a.py" in diff
    assert "+b" in diff
    assert "Patch unavailable" in diff


def test_fetch_diff_empty_pr_raises():
    with pytest.raises(GithubException):
        github_utils.fetch_pull_request_diff(_client([]), "o/r", 1)


@pytest.mark.parametrize("repo,number", [("bad", 1), ("o/r", 0)])
def test_fetch_diff_validates_input(repo, number):
    with pytest.raises(ValueError):
        github_utils.fetch_pull_request_diff(MagicMock(), repo, number)


def test_post_comment_returns_url():
    client = MagicMock()
    pr = client.get_repo.return_value.get_pull.return_value
    pr.create_issue_comment.return_value.html_url = "https://x/1"
    assert github_utils.post_pull_request_comment(client, "o/r", 2, " hi ") == "https://x/1"
    pr.create_issue_comment.assert_called_once_with("hi")


def test_post_comment_rejects_empty():
    with pytest.raises(ValueError):
        github_utils.post_pull_request_comment(MagicMock(), "o/r", 2, "  ")
