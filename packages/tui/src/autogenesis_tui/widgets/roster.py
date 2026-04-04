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
        yield Static("SHORTCUTS\nH hr  S standup\nU union  ? help", id="roster-shortcuts")

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

    def on_key(self, event: Key) -> None:
        if not self.rows:
            return
        current = self.selected_employee
        ids = [r.id for r in self.rows]
        if event.key == "up":
            if current is None:
                idx = len(ids) - 1
            else:
                idx = (ids.index(current) - 1) % len(ids) if current in ids else 0
            self.select(ids[idx])
            event.stop()
        elif event.key == "down":
            if current is None:
                idx = 0
            else:
                idx = (ids.index(current) + 1) % len(ids) if current in ids else 0
            self.select(ids[idx])
            event.stop()
        elif event.key == "enter":
            if current is not None:
                self.deselect()
            event.stop()

    def on_click(self, event: Click) -> None:
        if not self.rows:
            return
        # Determine which row was clicked by y offset within the roster list
        roster_list = self.query_one("#roster-list", Static)
        list_region = roster_list.region
        if list_region is None:
            return
        # y relative to the roster list widget
        rel_y = event.y - list_region.y
        if rel_y < 0 or rel_y >= len(self.rows):
            return
        row = self.rows[rel_y]
        if self.selected_employee == row.id:
            self.deselect()
        else:
            self.select(row.id)
        event.stop()
