"""Tests for CLI commands."""

from __future__ import annotations

from autogenesis_cli.app import app
from typer.testing import CliRunner

runner = CliRunner()


class TestCLIHelp:
    def test_help_shows_commands(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "login" in result.output
        assert "logout" in result.output
        assert "run" in result.output
        assert "chat" in result.output
        assert "config" in result.output

    def test_version_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestRunCommand:
    def test_run_help(self):
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "full-auto" in result.output
        assert "model" in result.output

    def test_run_without_prompt_fails(self):
        result = runner.invoke(app, ["run"], input="")
        assert result.exit_code == 1


class TestLoginCommand:
    def test_login_help(self):
        result = runner.invoke(app, ["login", "--help"])
        assert result.exit_code == 0
        assert "device-code" in result.output


class TestLogoutCommand:
    def test_logout_not_authenticated(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        result = runner.invoke(app, ["logout"])
        assert result.exit_code == 0
        assert (
            "nothing to do" in result.output.lower() or "not authenticated" in result.output.lower()
        )


class TestChatCommand:
    def test_chat_help(self):
        result = runner.invoke(app, ["chat", "--help"])
        assert result.exit_code == 0
        assert "full-auto" in result.output
        assert "model" in result.output

    def test_chat_exits_on_exit(self):
        result = runner.invoke(app, ["chat"], input="exit\n")
        assert result.exit_code == 0


class TestConfigCommand:
    def test_config_show(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        assert "codex" in result.output
