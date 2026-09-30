import pytest

import agents
import main
import tasks


def test_create_llm_requires_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValueError):
        agents.create_llm()


def test_create_llm_prefixes_groq_provider(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    assert agents.create_llm().model == "groq/openai/gpt-oss-120b"


def test_create_llm_rejects_bad_max_tokens(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_MAX_TOKENS", "abc")
    with pytest.raises(ValueError):
        agents.create_llm()


def test_build_crew_wires_three_agents_and_tasks(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    crew = main.build_crew()
    assert len(crew.agents) == 3
    assert len(crew.tasks) == 3
    assert crew.tasks[2].context == crew.tasks[:2]


def test_diff_with_braces_interpolates_safely(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    built = tasks.build_tasks(agents.build_agents())
    diff = '+d = {"key": "{value}"}\n+f"{x}"'
    for task in built:
        task.interpolate_inputs_and_add_conversation_history({"code_diff": diff})
        assert diff in task.description


def test_truncate_diff_keeps_short_diff_unchanged():
    assert main.truncate_diff("abc", 10) == "abc"


def test_truncate_diff_bounds_long_diff():
    out = main.truncate_diff("a" * 50 + "b" * 50, 20)
    assert out.startswith("a" * 10) and out.endswith("b" * 10)
    assert main.TRUNCATION_MARKER in out


def test_main_dry_run_does_not_post(monkeypatch, capsys):
    posted = []
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    fake_client = type("G", (), {"close": lambda self: None})()
    monkeypatch.setattr(main, "authenticate_github", lambda t: fake_client)
    monkeypatch.setattr(main, "fetch_pull_request_diff", lambda *a: "+x")
    monkeypatch.setattr(main, "run_review", lambda d: "LGTM")
    monkeypatch.setattr(main, "post_pull_request_comment", lambda *a: posted.append(a))
    assert main.main(["o/r", "1", "--dry-run"]) == 0
    assert "LGTM" in capsys.readouterr().out
    assert not posted


def test_main_returns_error_on_failure(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    assert main.main(["o/r", "1"]) == 1
