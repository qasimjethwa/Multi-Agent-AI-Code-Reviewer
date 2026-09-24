# Multi-Agent-AI-Code-Reviewer

## GitHub Actions setup

1. Add a repository secret named `GROQ_API_KEY` in **Settings > Secrets and variables > Actions**.
2. Enable Actions and open or update a pull request in the repository.
3. The `AI Code Reviewer` workflow runs the trusted default-branch code, reads the pull request diff through the GitHub API, and posts the generated review as a comment.

The workflow uses `llama-3.3-70b-versatile` through Groq. Fork pull requests are handled by `pull_request_target`, so the workflow must never be changed to execute pull-request code with repository secrets.