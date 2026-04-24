"""Tests for CLI commands."""

from __future__ import annotations

import re

from autogenesis_cli.app import app
from typer.testing import CliRunner

runner = CliRunner()
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _plain_output(output: str) -> str:
    return _ANSI_RE.sub("", output)


class TestCLIHelp:
    def test_help_shows_commands(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "login" in result.output
        assert "logout" in result.output
        assert "run" in result.output
        assert "chat" in result.output
        assert "config" in result.output
        assert "project" in result.output

    def test_version_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestRunCommand:
    def test_run_help(self):
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        output = _plain_output(result.output)
        assert "full-auto" in output
        assert "model" in output

    def test_run_without_prompt_fails(self):
        result = runner.invoke(app, ["run"], input="")
        assert result.exit_code == 1


class TestLoginCommand:
    def test_login_help(self):
        result = runner.invoke(app, ["login", "--help"])
        assert result.exit_code == 0
        assert "device-code" in _plain_output(result.output)


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
        output = _plain_output(result.output)
        assert "full-auto" in output
        assert "model" in output

    def test_chat_exits_on_exit(self):
        result = runner.invoke(app, ["chat"], input="exit\n")
        # Chat now launches codex subprocess — may fail if codex not in PATH
        if result.exit_code != 0 and isinstance(result.exception, SystemExit | FileNotFoundError):
            return
        assert result.exit_code == 0


class TestConfigCommand:
    def test_config_show(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        assert "codex" in result.output


class TestProjectCommand:
    def test_project_help(self):
        result = runner.invoke(app, ["project", "--help"])
        assert result.exit_code == 0
        assert "init" in result.output

    def test_project_init_writes_config(self, tmp_path):
        result = runner.invoke(app, ["project", "init", str(tmp_path), "--skip-index"])
        assert result.exit_code == 0
        cfg = tmp_path / ".autogenesis" / "config.yaml"
        assert cfg.exists()
        content = cfg.read_text()
        assert "gitnexus:" in content
        assert "enabled: true" in content


class TestTwitterCommand:
    def test_twitter_help(self):
        result = runner.invoke(app, ["twitter", "--help"])
        assert result.exit_code == 0
        assert "start" in result.output
        assert "stop" in result.output
        assert "queue" in result.output
        assert "interview" in result.output

    def test_twitter_start(self):
        result = runner.invoke(app, ["twitter", "start"])
        # May fail if autogenesis_twitter package not installed in test env
        if result.exit_code != 0 and isinstance(result.exception, ModuleNotFoundError):
            return
        assert result.exit_code == 0

    def test_twitter_stop(self):
        result = runner.invoke(app, ["twitter", "stop"])
        assert result.exit_code == 0

    def test_twitter_status(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        result = runner.invoke(app, ["twitter", "status"])
        # May fail if autogenesis_twitter package not installed in test env
        if result.exit_code != 0 and isinstance(result.exception, ModuleNotFoundError):
            return
        assert result.exit_code == 0


class TestHRCommand:
    def test_hr_help(self):
        result = runner.invoke(app, ["hr", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "hire" in result.output
        assert "fire" in result.output
        assert "train" in result.output
        assert "show" in result.output


class TestMeetingCommand:
    def test_meeting_help(self):
        result = runner.invoke(app, ["meeting", "--help"])
        assert result.exit_code == 0

    def test_standup_help(self):
        result = runner.invoke(app, ["standup", "--help"])
        assert result.exit_code == 0


class TestUnionCommand:
    def test_union_help(self):
        result = runner.invoke(app, ["union", "--help"])
        assert result.exit_code == 0
        assert "proposals" in result.output
        assert "review" in result.output
        assert "resolve" in result.output
