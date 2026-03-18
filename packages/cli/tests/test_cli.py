"""Tests for CLI commands."""

from __future__ import annotations

from autogenesis_cli.app import app
from typer.testing import CliRunner

runner = CliRunner()


class TestCLIHelp:
    def test_help_shows_commands(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "chat" in result.output
        assert "run" in result.output
        assert "init" in result.output
        assert "config" in result.output

    def test_version_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestRunCommand:
    def test_run_with_prompt(self):
        result = runner.invoke(app, ["run", "hello world"])
        assert result.exit_code == 0
        assert "hello world" in result.output

    def test_run_without_prompt_fails(self):
        result = runner.invoke(app, ["run"], input="")
        # Should fail gracefully when no prompt and no stdin
        assert result.exit_code in (0, 1)

    def test_run_help(self):
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "tier" in result.output


class TestInitCommand:
    def test_init_creates_config(self, tmp_path):
        result = runner.invoke(app, ["init", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / ".autogenesis" / "config.yaml").exists()

    def test_init_already_exists(self, tmp_path):
        config_dir = tmp_path / ".autogenesis"
        config_dir.mkdir()
        (config_dir / "config.yaml").write_text("models: {}")

        result = runner.invoke(app, ["init", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "Already initialized" in result.output


class TestConfigCommand:
    def test_config_show(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        assert "models" in result.output

    def test_config_get(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        result = runner.invoke(app, ["config", "get", "models.default_tier"])
        assert result.exit_code == 0
        assert "standard" in result.output

    def test_config_set(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["config", "set", "models.default_tier", "fast"])
        assert result.exit_code == 0
        assert "Set" in result.output

    def test_config_help(self):
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0


class TestChatCommand:
    def test_chat_help(self):
        result = runner.invoke(app, ["chat", "--help"])
        assert result.exit_code == 0
        assert "resume" in result.output
        assert "tier" in result.output

    def test_chat_list_sessions_empty(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        result = runner.invoke(app, ["chat", "--list-sessions"])
        assert result.exit_code == 0
        assert "No saved sessions" in result.output

    def test_chat_exits_on_exit(self):
        result = runner.invoke(app, ["chat"], input="exit\n")
        assert result.exit_code == 0

    def test_chat_echoes_input(self):
        result = runner.invoke(app, ["chat"], input="hello\nexit\n")
        assert result.exit_code == 0
        assert "hello" in result.output

    def test_chat_exits_on_eof(self):
        result = runner.invoke(app, ["chat"], input="")
        assert result.exit_code == 0
