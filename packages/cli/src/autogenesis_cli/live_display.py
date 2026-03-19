"""Live terminal display for CEO orchestrator — shows active sub-agents in real-time."""

from __future__ import annotations

import threading
import time
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

_SPINNER_FRAMES = ["   ", ".  ", ".. ", "..."]


class AgentLiveDisplay:
    """Real-time dashboard of active sub-agents with animated spinners."""

    def __init__(self) -> None:
        self._agents: dict[str, dict[str, Any]] = {}
        self._completed: list[dict[str, Any]] = []
        self._console = Console(stderr=True)
        self._live: Live | None = None
        self._phase = ""
        self._frame = 0
        self._ticker: threading.Thread | None = None
        self._running = False

    def start(self) -> None:
        """Start the live display with background animation ticker."""
        self._live = Live(
            self._render(),
            console=self._console,
            refresh_per_second=8,
            transient=False,
        )
        self._live.start()
        self._running = True
        self._ticker = threading.Thread(target=self._animation_loop, daemon=True)
        self._ticker.start()

    def _animation_loop(self) -> None:
        """Background thread that ticks the animation forward."""
        while self._running:
            time.sleep(0.25)
            self._frame += 1
            self._refresh()

    def stop(self) -> None:
        """Stop the live display and animation."""
        self._running = False
        if self._ticker:
            self._ticker.join(timeout=1)
            self._ticker = None
        if self._live:
            self._live.stop()
            self._live = None

    def set_phase(self, phase: str) -> None:
        """Set the current orchestration phase."""
        self._phase = phase
        self._refresh()

    def agent_start(self, label: str, task: str) -> None:
        """Mark an agent as active with its current task."""
        self._agents[label] = {"task": task, "detail": ""}
        self._refresh()

    def agent_update(self, label: str, detail: str) -> None:
        """Update an agent's current activity detail."""
        if label in self._agents:
            self._agents[label]["detail"] = detail
            self._refresh()

    def agent_done(self, label: str, result: str = "done") -> None:
        """Mark an agent as completed."""
        if label in self._agents:
            entry = self._agents.pop(label)
            self._completed.append({"label": label, "task": entry["task"], "result": result})
            self._refresh()

    def _spinner(self) -> str:
        return _SPINNER_FRAMES[self._frame % len(_SPINNER_FRAMES)]

    def _render(self) -> Table:
        """Render the current state as a Rich Table."""
        table = Table(
            show_header=False,
            show_edge=False,
            pad_edge=False,
            box=None,
            expand=True,
        )
        table.add_column("indicator", width=4, no_wrap=True)
        table.add_column("label", width=22, no_wrap=True)
        table.add_column("info", ratio=1)

        spinner = self._spinner()

        if self._phase:
            table.add_row(
                Text(spinner, style="bold yellow"),
                Text("CEO", style="bold yellow"),
                Text(self._phase, style="yellow"),
            )

        for label, info in self._agents.items():
            detail = info["detail"] or info["task"]
            if len(detail) > 80:  # noqa: PLR2004
                detail = detail[:77] + "..."
            table.add_row(
                Text(spinner, style="bold cyan"),
                Text(label, style="bold cyan"),
                Text(detail, style="dim"),
            )

        for entry in self._completed[-5:]:
            result_text = entry["result"]
            if len(result_text) > 60:  # noqa: PLR2004
                result_text = result_text[:57] + "..."
            table.add_row(
                Text(" \u2713  ", style="bold green"),
                Text(entry["label"], style="green"),
                Text(result_text, style="dim green"),
            )

        return table

    def _refresh(self) -> None:
        if self._live:
            self._live.update(self._render())
