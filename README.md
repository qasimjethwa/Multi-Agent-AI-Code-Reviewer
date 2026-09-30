# Multi-Agent AI Code Reviewer

Automatically reviews GitHub pull requests with three [CrewAI](https://docs.crewai.com) agents running on [Groq](https://groq.com):

1. **Security reviewer** – OWASP risks, injection, auth, secrets, unsafe input handling.
2. **Performance & quality reviewer** – complexity, resource usage, correctness, PEP 8.
3. **Documentation & synthesis specialist** – merges both reviews into one Markdown comment.

The reviewer fetches the PR diff through the GitHub API and posts the result as a PR comment.

## GitHub Actions setup (deployment)

1. Add a repository secret **`GROQ_API_KEY`** in **Settings → Secrets and variables → Actions**.
2. *(Optional)* Add a repository **variable** `GROQ_MODEL` to override the default `openai/gpt-oss-120b`.
3. Open or update a non-draft pull request. The **AI Code Reviewer** workflow posts a review comment.

`GITHUB_TOKEN` is supplied automatically by Actions. The workflow uses `pull_request_target` and always
checks out the trusted default branch, so fork PRs are reviewed without executing their code with
repository secrets. Never change it to check out PR code.

## Local usage

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # fill in GITHUB_TOKEN and GROQ_API_KEY
python main.py owner/repo 123 --dry-run   # print the review instead of posting
python main.py owner/repo 123             # post the review as a PR comment
```

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `GITHUB_TOKEN` | yes | Read the PR diff and post the comment (auto-provided in Actions; locally a fine-grained PAT with Pull requests: read & write). |
| `GROQ_API_KEY` | yes | Groq API key. Actions secret. |
| `GROQ_MODEL` | no | Groq model id (default `openai/gpt-oss-120b`). |
| `GROQ_MAX_TOKENS` | no | Max response tokens per agent call (default 1024). |
| `MAX_DIFF_CHARS` | no | Max diff characters sent to the agents (default 6000); larger diffs keep head and tail. |
| `LOG_LEVEL` | no | Logging level (default `INFO`). |

## Development

```bash
ruff check . && ruff format --check .
pytest
```

CI (`.github/workflows/ci.yml`) runs lint and tests on Python 3.11 and 3.12 for every push and PR.

## AI Reviewer Test

AI reviewer workflow retest
