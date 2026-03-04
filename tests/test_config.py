import os

from gcpclaw.config import _env_bool, validate_config


def test_env_bool_true(monkeypatch):
    monkeypatch.setenv("TEST_FLAG", "true")
    assert _env_bool("TEST_FLAG") is True


def test_env_bool_false(monkeypatch):
    monkeypatch.setenv("TEST_FLAG", "false")
    assert _env_bool("TEST_FLAG") is False


def test_env_bool_default():
    os.environ.pop("TEST_FLAG_MISSING", None)
    assert _env_bool("TEST_FLAG_MISSING", default=True) is True


def test_validate_config_warns_missing_key(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENT_MODEL", "openai/gpt-4o")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("WORKSPACE_DIR", str(tmp_path))
    warnings = validate_config()
    assert any("OPENAI_API_KEY" in warning for warning in warnings)
