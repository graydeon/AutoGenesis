from __future__ import annotations

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


@dataclass
class GoalEntry:
    id: str
    description: str
    completed: int
    total: int
    status: str = "executing"


class RightPanel(Widget):
    """Right column — Goals/Tokens view or Employee Detail view."""

    DEFAULT_CSS = """
    RightPanel {
        width: 24;
        height: 100%;
        background: $surface;
        overflow-y: auto;
        padding: 0 1;
    }
    """

    mode: reactive[str] = reactive("goals")
    session_tokens: reactive[int] = reactive(0)
    daily_tokens: reactive[int] = reactive(0)
    focused_employee: reactive[str | None] = reactive(None)

    class BackToGoals(Message):
        pass

    def __init__(self) -> None:
        super().__init__()
        self.goals: list[GoalEntry] = []
        self._employee_data: dict[str, object] = {}

    def compose(self) -> ComposeResult:
        yield Static("", id="panel-content")

    def update_goals(self, goals: list[GoalEntry]) -> None:
        self.goals = list(goals)
        if self.mode == "goals":
            self._refresh()

    def update_tokens(self, session: int, daily: int = 0) -> None:
        self.session_tokens = session
        self.daily_tokens = daily
        if self.mode == "goals":
            self._refresh()

    def show_goals(self) -> None:
        self.mode = "goals"
        self.focused_employee = None
        self._refresh()

    def show_employee(
        self,
        employee_id: str,
        memories: list[str],
        inbox_count: int,
        training: list[str],
    ) -> None:
        self.mode = "employee"
        self.focused_employee = employee_id
        self._employee_data = {
            "memories": memories,
            "inbox_count": inbox_count,
            "training": training,
        }
        self._refresh()

    def _refresh(self) -> None:
        content = self.query_one("#panel-content", Static)
        if self.mode == "goals":
            content.update(self._render_goals())
        else:
            content.update(self._render_employee())

    def _render_goals(self) -> str:
        lines = ["GOALS"]
        for g in self.goals:
            bar_filled = int((g.completed / g.total) * 10) if g.total else 0
            bar = "█" * bar_filled + "░" * (10 - bar_filled)
            lines.append(f"⟳ {g.description[:18]}")
            lines.append(f"  [{bar}] {g.completed}/{g.total}")
        lines += ["", "TOKENS", f"Session: {self.session_tokens:,}", f"Daily:   {self.daily_tokens:,}"]
        return "\n".join(lines)

    def _render_employee(self) -> str:
        emp = self.focused_employee or ""
        memories = list(self._employee_data.get("memories", []))  # type: ignore[arg-type]
        inbox_count = int(self._employee_data.get("inbox_count", 0))  # type: ignore[arg-type]
        training = list(self._employee_data.get("training", []))  # type: ignore[arg-type]
        lines = [f"▶ {emp}", ""]
        if memories:
            lines += ["BRAIN (top memories)"] + [f"• {m[:20]}" for m in memories[:5]]
        lines += ["", f"INBOX  {inbox_count} unread"]
        if training:
            lines += ["", "TRAINING"] + [f"• {t[:20]}" for t in training[:3]]
        lines += ["", "← back to goals"]
        return "\n".join(lines)
