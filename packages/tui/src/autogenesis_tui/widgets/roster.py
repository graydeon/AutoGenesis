from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.events import Click, Key

_STATUS_ICONS = {
    "idle": ("○", "dim"),
    "working": ("⟳", "warning"),
    "done": ("✓", "success"),
    "active": ("●", "success"),
}


@dataclass
class EmployeeRow:
    id: str
    title: str
    status: str = "idle"
    detail: str = ""


class EmployeeRoster(Widget):
    """Left column: scrollable employee list with status indicators."""

    DEFAULT_CSS = """
    EmployeeRoster {
        width: 22;
        height: 100%;
        background: $surface;
        overflow-y: auto;
    }
    """

    selected_employee: reactive[str | None] = reactive(None)

    class Selected(Message):
        def __init__(self, employee_id: str | None) -> None:
            super().__init__()
            self.employee_id = employee_id

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[EmployeeRow] = []

    def compose(self) -> ComposeResult:
        yield Static("EMPLOYEES", id="roster-header")
        yield Static("", id="roster-list")
        yield Static(
            "NAV: ↑↓ PGUP/PGDN HOME/END\n"
            "ESC/TAB: leave input box\n"
            "H hr  S standup  U union\n"
            "? help  ENTER select",
            id="roster-shortcuts",
        )

    def load(self, rows: list[EmployeeRow]) -> None:
        self.rows = list(rows)
        self._refresh_list()

    def _refresh_list(self) -> None:
        roster_list = self.query_one("#roster-list", Static)
        lines = []
        for row in self.rows:
            icon, _ = _STATUS_ICONS.get(row.status, ("○", "dim"))
            selected = " ▶" if row.id == self.selected_employee else ""
            lines.append(f"{icon} {row.id}{selected}")
        roster_list.update("\n".join(lines))

    def set_status(self, employee_id: str, status: str) -> None:
        for row in self.rows:
            if row.id == employee_id:
                row.status = status
                break
        self._refresh_list()

    def set_detail(self, employee_id: str, detail: str) -> None:
        for row in self.rows:
            if row.id == employee_id:
                row.detail = detail
                break
        self._refresh_list()

    def select(self, employee_id: str | None) -> None:
        self.selected_employee = employee_id
        self._refresh_list()
        self.post_message(self.Selected(employee_id))

    def deselect(self) -> None:
        self.select(None)

    def _selected_index(self, ids: list[str]) -> int | None:
        current = self.selected_employee
        return ids.index(current) if current in ids else None

    def _select_relative(self, ids: list[str], offset: int, *, wrap: bool = False) -> None:
        idx = self._selected_index(ids)
        if idx is None:
            idx = 0 if offset > 0 else len(ids) - 1
        elif wrap:
            idx = (idx + offset) % len(ids)
        else:
            idx = min(len(ids) - 1, max(0, idx + offset))
        self.select(ids[idx])

    def on_key(self, event: Key) -> None:
        if not self.rows:
            return
        ids = [r.id for r in self.rows]
        key = event.key

        if key in ("up", "down"):
            self._select_relative(ids, -1 if key == "up" else 1, wrap=True)
        elif key in ("pageup", "ctrl+b", "pagedown", "ctrl+f"):
            self._select_relative(ids, -5 if key in ("pageup", "ctrl+b") else 5)
        elif key == "home":
            self.select(ids[0])
        elif key == "end":
            self.select(ids[-1])
        elif key == "enter":
            self.deselect()
        else:
            return
        event.stop()

    def on_click(self, event: Click) -> None:
        if not self.rows:
            return
        # Calculate which row was clicked based on cursor position within the list
        # event.y is relative to this EmployeeRoster widget
        roster_list = self.query_one("#roster-list", Static)
        list_region = roster_list.region
        if list_region is None:
            return
        # The row index is the click y-position minus the list's top offset
        # Minus 1 to account for widget border/padding offset that causes the 2-row drift
        rel_y = event.y - list_region.y - 1
        scroll_y = roster_list.scroll_offset.y
        rel_y += scroll_y
        if rel_y < 0 or rel_y >= len(self.rows):
            return
        row = self.rows[rel_y]
        if self.selected_employee == row.id:
            self.deselect()
        else:
            self.select(row.id)
        event.stop()
