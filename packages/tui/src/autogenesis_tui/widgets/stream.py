from __future__ import annotations

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


@dataclass
class StreamEntry:
    source: str
    text: str = ""
    is_tool: bool = False
    tool_name: str = ""
    tool_arg: str = ""
    tool_success: bool = True
    turn_id: str = ""
    complete: bool = False


class AgentStream(Widget):
    """Center column: scrolling log of agent activity with source filtering."""

    DEFAULT_CSS = """
    AgentStream {
        width: 1fr;
        height: 100%;
        background: $background;
        overflow-y: auto;
    }
    """

    active_filter: reactive[str | None] = reactive(None)

    def __init__(self) -> None:
        super().__init__()
        self.entries: list[StreamEntry] = []
        self._current_entry: dict[str, StreamEntry] = {}

    def compose(self) -> ComposeResult:
        yield Static("ALL", id="filter-bar")
        yield Static("", id="stream-body")

    def add_agent_delta(self, delta: str, source: str, turn_id: str) -> None:
        if turn_id not in self._current_entry:
            entry = StreamEntry(source=source, turn_id=turn_id)
            self.entries.append(entry)
            self._current_entry[turn_id] = entry
        self._current_entry[turn_id].text += delta
        self._refresh_body()

    def complete_turn(self, turn_id: str) -> None:
        entry = self._current_entry.pop(turn_id, None)
        if entry:
            entry.complete = True
        self._refresh_body()

    def add_tool_block(
        self,
        tool_name: str,
        tool_arg: str,
        success: bool,
        source: str,
        turn_id: str = "",
    ) -> None:
        entry = StreamEntry(
            source=source,
            is_tool=True,
            tool_name=tool_name,
            tool_arg=tool_arg,
            tool_success=success,
            turn_id=turn_id,
            complete=True,
        )
        self.entries.append(entry)
        self._refresh_body()

    def set_filter(self, source: str | None) -> None:
        self.active_filter = source
        self._refresh_body()

    def _entry_visible(self, entry: StreamEntry) -> bool:
        if self.active_filter is None:
            return True
        return entry.source == self.active_filter

    def _refresh_body(self) -> None:
        lines: list[str] = []
        for entry in self.entries:
            if not self._entry_visible(entry):
                continue
            if entry.is_tool:
                result = "→ ok" if entry.tool_success else "→ error"
                lines.append(f"  ▸ {entry.tool_name}  {entry.tool_arg}")
                lines.append(f"  {result}")
            else:
                suffix = " ✓" if entry.complete else ""
                lines.append(f"{entry.source} › {entry.text}{suffix}")
        self.query_one("#stream-body", Static).update("\n".join(lines))
