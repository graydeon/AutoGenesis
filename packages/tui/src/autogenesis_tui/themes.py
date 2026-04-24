from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from textual.theme import Theme

_BUILTIN_DIR = Path(__file__).parent / "themes"

# Palette indices used for per-employee accent color cycling.
# Maps roster position → color key from theme dict.
EMPLOYEE_PALETTE_KEYS = ["success", "warning", "accent", "error", "text"]
ThemeData = dict[str, str]


class ThemeManager:
    """Loads built-in and user TOML themes, converts to Textual Theme objects."""

    def __init__(self, user_themes_dir: Path | None = None) -> None:
        self._themes: dict[str, ThemeData] = {}
        self._load_dir(_BUILTIN_DIR)
        if user_themes_dir and user_themes_dir.is_dir():
            self._load_dir(user_themes_dir)

    def _load_dir(self, directory: Path) -> None:
        for path in directory.glob("*.toml"):
            with path.open("rb") as f:
                data: dict[str, Any] = tomllib.load(f)
            palette = data.get("theme", data)
            if not isinstance(palette, dict):
                continue
            theme = {str(k): str(v) for k, v in palette.items()}
            name = theme.get("name", path.stem)
            self._themes[name] = theme

    def list_theme_names(self) -> list[str]:
        return list(self._themes.keys())

    def get_theme(self, name: str) -> ThemeData:
        if name not in self._themes:
            raise KeyError(name)
        return self._themes[name]

    def to_textual_theme(self, name: str) -> Theme:
        t = self.get_theme(name)
        return Theme(
            name=name,
            dark=True,
            primary=t["accent"],
            secondary=t["subtext"],
            warning=t["warning"],
            error=t["error"],
            success=t["success"],
            background=t["background"],
            surface=t["surface"],
            panel=t["border"],
        )

    def employee_color(self, index: int, theme_name: str) -> str:
        """Return a stable accent color for an employee at roster index."""
        t = self.get_theme(theme_name)
        key = EMPLOYEE_PALETTE_KEYS[index % len(EMPLOYEE_PALETTE_KEYS)]
        return t[key]
