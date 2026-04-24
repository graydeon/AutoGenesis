from __future__ import annotations

from pathlib import Path  # noqa: TC003

import pytest
from autogenesis_tui.themes import ThemeManager


def test_builtin_themes_loaded():
    mgr = ThemeManager()
    names = mgr.list_theme_names()
    assert "dracula" in names
    assert "midnight-blue" in names
    assert "hacker-green" in names


def test_get_theme_returns_dict():
    mgr = ThemeManager()
    t = mgr.get_theme("dracula")
    assert t["background"] == "#282a36"
    assert t["surface"] == "#21222c"
    assert t["accent"] == "#bd93f9"
    assert t["success"] == "#50fa7b"
    assert t["warning"] == "#f1fa8c"
    assert t["error"] == "#ff5555"
    assert t["text"] == "#f8f8f2"
    assert t["subtext"] == "#6272a4"
    assert t["border"] == "#44475a"


def test_unknown_theme_raises():
    mgr = ThemeManager()
    with pytest.raises(KeyError, match="unknown-theme"):
        mgr.get_theme("unknown-theme")


def test_user_theme_loaded(tmp_path: Path):
    theme_dir = tmp_path / "themes"
    theme_dir.mkdir()
    (theme_dir / "custom.toml").write_text(
        '[theme]\nname = "custom"\nbackground = "#000000"\n'
        'surface = "#111111"\naccent = "#ffffff"\nsuccess = "#00ff00"\n'
        'warning = "#ffff00"\nerror = "#ff0000"\ntext = "#eeeeee"\n'
        'subtext = "#888888"\nborder = "#333333"\n'
    )
    mgr = ThemeManager(user_themes_dir=theme_dir)
    assert "custom" in mgr.list_theme_names()


def test_to_textual_theme():
    mgr = ThemeManager()
    t = mgr.to_textual_theme("dracula")
    # Import here to avoid slow import at test collection time
    from textual.theme import Theme

    assert isinstance(t, Theme)
    assert t.name == "dracula"
