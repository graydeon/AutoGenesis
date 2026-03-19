"""Live terminal display for CEO orchestrator — shows active sub-agents in real-time."""

from __future__ import annotations

import contextlib
import threading
import time
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

_SPINNER_FRAMES = ["   ", ".  ", ".. ", "..."]


class AgentLiveDisplay:
    """Real-time dashboard of active sub-agents with animated spinners.

    Thread-safe: state mutations set a dirty flag, only the animation
    thread touches Rich Live.update().
    """

    def __init__(self) -> None:
        self._agents: dict[str, dict[str, Any]] = {}
        self._completed: list[dict[str, Any]] = []
        self._console = Console(stderr=True)
        self._live: Live | None = None
        self._phase = ""
        self._frame = 0
        self._lock = threading.Lock()
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
        """Background thread — sole owner of Live.update()."""
        while self._running:
            time.sleep(0.25)
            self._frame += 1
            with self._lock, contextlib.suppress(Exception):
                if self._live:
                    self._live.update(self._render())

    def stop(self) -> None:
        """Stop the live display and animation."""
        self._running = False
        if self._ticker:
            self._ticker.join(timeout=2)
            self._ticker = None
        if self._live:
            with contextlib.suppress(Exception):
                self._live.stop()
            self._live = None

    def set_phase(self, phase: str) -> None:
        """Set the current orchestration phase."""
        with self._lock:
            self._phase = phase

    def agent_start(self, label: str, task: str) -> None:
        """Mark an agent as active with its current task."""
        with self._lock:
            self._agents[label] = {"task": task, "detail": ""}

    def agent_update(self, label: str, detail: str) -> None:
        """Update an agent's current activity detail."""
        with self._lock:
            if label in self._agents:
                self._agents[label]["detail"] = detail

    def agent_done(self, label: str, result: str = "done") -> None:
        """Mark an agent as completed."""
        with self._lock:
            if label in self._agents:
                entry = self._agents.pop(label)
                self._completed.append({"label": label, "task": entry["task"], "result": result})

    def _spinner(self) -> str:
        return _SPINNER_FRAMES[self._frame % len(_SPINNER_FRAMES)]

    def _render(self) -> Table:
        """Render the current state as a Rich Table. Called under lock."""
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

        for label, info in list(self._agents.items()):
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
