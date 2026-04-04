from __future__ import annotations

import os
from pathlib import Path
from typing import Any, ClassVar

import structlog
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal

from autogenesis_tui.client import CodexWSClient
from autogenesis_tui.server import AppServerManager
from autogenesis_tui.themes import ThemeManager
from autogenesis_tui.widgets import (
    AgentStream,
    EmployeeRoster,
    InputBar,
    RightPanel,
    StatusBar,
)
from autogenesis_tui.widgets.roster import EmployeeRow

logger = structlog.get_logger()

_CEO_SYSTEM_PROMPT = """\
You are the CEO Orchestrator of AutoGenesis — an autonomous multi-agent software startup.
Decompose high-level goals into subtasks, assign to the right employee, dispatch via
`ceo run`, and adapt based on results. Use `autogenesis hr list` to see your team.
"""


class AutogenesisApp(App[None]):
    """Three-column AutoGenesis TUI — Command Center layout."""

    CSS = """
    Screen {
        layout: vertical;
    }
    StatusBar {
        dock: top;
        height: 1;
    }
    InputBar {
        dock: bottom;
        height: 3;
    }
    #columns {
        height: 1fr;
        layout: horizontal;
    }
    EmployeeRoster {
        width: 22;
        border-right: solid $border;
    }
    AgentStream {
        width: 1fr;
    }
    RightPanel {
        width: 26;
        border-left: solid $border;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("ctrl+g", "new_goal", "New Goal"),
        Binding("ctrl+n", "new_thread", "New Thread"),
        Binding("t", "theme_picker", "Theme", show=False),
        Binding("escape", "deselect_employee", "Deselect", show=False),
        Binding("g", "stream_bottom", "Stream Bottom", show=False),
        Binding("question_mark", "help", "Help", show=False),
    ]

    def __init__(self, *, auto_start: bool = True, theme_name: str = "dracula") -> None:
        super().__init__()
        self._auto_start = auto_start
        self._theme_name = theme_name
        self._server = AppServerManager()
        self._client: CodexWSClient | None = None
        self._theme_mgr = ThemeManager(
            user_themes_dir=Path.home() / ".config" / "autogenesis" / "themes"
        )
        self._active_thread_id: str | None = None
        self._employee_threads: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        yield StatusBar()
        with Horizontal(id="columns"):
            yield EmployeeRoster()
            yield AgentStream()
            yield RightPanel()
        yield InputBar()

    async def on_mount(self) -> None:
        # Register and apply theme
        for name in self._theme_mgr.list_theme_names():
            self.register_theme(self._theme_mgr.to_textual_theme(name))
        self.theme = self._theme_name

        await self._load_employees()
        self._subscribe_event_bus()

        if self._auto_start:
            await self._start_server()

    async def _start_server(self) -> None:
        status = self.query_one(StatusBar)
        status.update_connection("connecting")
        try:
            port = await self._server.start()
            self._client = CodexWSClient(port=port, on_event=self.handle_ws_event)
            await self._client.connect()
            self._active_thread_id = await self._client.start_thread(
                base_instructions=_CEO_SYSTEM_PROMPT,
                cwd=str(Path.cwd()),
            )
            status.update_connection("connected")
        except Exception as exc:  # noqa: BLE001
            logger.warning("app_server_start_failed", exc=str(exc))
            status.update_connection("disconnected")

    async def _load_employees(self) -> None:
        try:
            from autogenesis_core.config import load_config
            from autogenesis_employees.registry import EmployeeRegistry

            cfg = load_config()
            xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
            global_dir = (
                Path(cfg.employees.global_roster_path)
                if cfg.employees.global_roster_path
                else Path(xdg) / "autogenesis" / "employees"
            )
            registry = EmployeeRegistry(global_dir=global_dir)
            rows = [
                EmployeeRow(id=e.id, title=e.title, status="idle") for e in registry.list_active()
            ]
            self.query_one(EmployeeRoster).load(rows)
            targets = ["CEO"] + [r.id for r in rows]
            self.query_one(InputBar).load_targets(targets)
        except Exception as exc:  # noqa: BLE001
            logger.warning("employee_load_failed", exc=str(exc))

    def _subscribe_event_bus(self) -> None:
        try:
            from autogenesis_core.events import EventType, get_event_bus

            bus = get_event_bus()
            bus.subscribe(EventType.CEO_SUBTASK_ASSIGN, self._on_subtask_assign)
            bus.subscribe(EventType.CEO_SUBTASK_COMPLETE, self._on_subtask_complete)
            bus.subscribe(EventType.CEO_SUBTASK_FAIL, self._on_subtask_fail)
        except Exception as exc:  # noqa: BLE001
            logger.warning("event_bus_subscribe_failed", exc=str(exc))

    def _on_subtask_assign(self, event: Any) -> None:  # noqa: ANN401
        emp = event.data.get("employee_id", "")
        task = event.data.get("subtask", "")[:60]
        self.call_from_thread(self.query_one(EmployeeRoster).set_status, emp, "working")
        self.call_from_thread(
            self.query_one(AgentStream).add_agent_delta,
            f"Assigned: {task}",
            emp,
            f"assign-{emp}",
        )

    def _on_subtask_complete(self, event: Any) -> None:  # noqa: ANN401
        emp = event.data.get("employee_id", "")
        self.call_from_thread(self.query_one(EmployeeRoster).set_status, emp, "done")

    def _on_subtask_fail(self, event: Any) -> None:  # noqa: ANN401
        emp = event.data.get("employee_id", "")
        self.call_from_thread(self.query_one(EmployeeRoster).set_status, emp, "idle")

    def handle_ws_event(self, event: dict[str, Any]) -> None:
        """Route a WebSocket notification to the UI. Safe to call from any context."""
        self.call_after_refresh(self._process_ws_event, event)

    def _process_ws_event(self, event: dict[str, Any]) -> None:
        method = event.get("method", "")
        params = event.get("params", {})
        stream = self.query_one(AgentStream)
        status = self.query_one(StatusBar)

        if method == "item/agentMessage/delta":
            stream.add_agent_delta(params.get("delta", ""), "CEO", params.get("turnId", ""))
        elif method == "item/commandExecution/outputDelta":
            stream.add_tool_block(
                tool_name="shell",
                tool_arg=str(params.get("delta", ""))[:40],
                success=True,
                source="CEO",
                turn_id=params.get("turnId", ""),
            )
        elif method == "turn/completed":
            turn = params.get("turn", {})
            stream.complete_turn(str(turn.get("id", "")))
            status.update_connection("connected")
        elif method == "turn/started":
            status.update_connection("connected")
        elif method == "thread/tokenUsage/updated":
            total = int(params.get("tokenUsage", {}).get("total", {}).get("totalTokens", 0))
            status.update_tokens(total)
            self.query_one(RightPanel).update_tokens(session=total)
        elif method == "thread/started":
            thread = params.get("thread", {})
            model = str(thread.get("source", ""))
            if model:
                status.update_connection("connected", model)

    async def on_input_bar_submitted(self, event: InputBar.Submitted) -> None:
        if not self._client:
            return
        text = event.text
        thread_id = self._employee_threads.get(event.target, self._active_thread_id)
        if thread_id:
            self.query_one(AgentStream).add_agent_delta(f"> {text}", "you", "input")
            await self._client.send_turn(thread_id, text)

    async def on_employee_roster_selected(self, event: EmployeeRoster.Selected) -> None:
        emp_id = event.employee_id
        stream = self.query_one(AgentStream)
        right = self.query_one(RightPanel)
        input_bar = self.query_one(InputBar)

        if emp_id is None:
            stream.set_filter(None)
            right.show_goals()
            input_bar.set_target("CEO")
            return

        stream.set_filter(emp_id)
        input_bar.set_target(emp_id)
        await self._show_employee_detail(emp_id)

    async def _show_employee_detail(self, emp_id: str) -> None:
        right = self.query_one(RightPanel)
        try:
            from autogenesis_employees.brain import BrainManager
            from autogenesis_employees.inbox import InboxManager

            base_dir = Path.cwd() / ".autogenesis"
            data_dir = base_dir / "employees" / emp_id
            brain = BrainManager(data_dir / "brain.db")
            inbox = InboxManager(data_dir / "inbox.db")
            await brain.initialize()
            await inbox.initialize()
            memories = [m.content for m in await brain.top_memories(5)]
            unread = await inbox.get_unread(emp_id)
            await brain.close()
            await inbox.close()

            xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
            global_dir = Path(xdg) / "autogenesis" / "employees"
            from autogenesis_employees.registry import EmployeeRegistry

            registry = EmployeeRegistry(global_dir=global_dir)
            emp_config = registry.get(emp_id)
            training = emp_config.training_directives if emp_config else []

            right.show_employee(
                employee_id=emp_id,
                memories=memories,
                inbox_count=len(unread),
                training=training,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("employee_detail_failed", emp=emp_id, exc=str(exc))
            right.show_employee(emp_id, [], 0, [])

    async def action_new_goal(self) -> None:
        self.query_one(InputBar).set_target("CEO")
        self.query_one("#chat-input").focus()

    async def action_new_thread(self) -> None:
        if self._client and self._active_thread_id:
            new_id = await self._client.fork_thread(self._active_thread_id)
            self._active_thread_id = new_id

    async def action_interrupt(self) -> None:
        if self._client and self._active_thread_id:
            await self._client.interrupt(self._active_thread_id)

    def action_deselect_employee(self) -> None:
        self.query_one(EmployeeRoster).deselect()

    def action_stream_bottom(self) -> None:
        self.query_one(AgentStream).scroll_end()

    def action_theme_picker(self) -> None:
        names = self._theme_mgr.list_theme_names()
        current_idx = names.index(self.theme) if self.theme in names else 0
        next_name = names[(current_idx + 1) % len(names)]
        self.theme = next_name

    def action_help(self) -> None:
        self.notify(
            "Ctrl+G new goal · Ctrl+N new thread · T theme · "
            "Esc deselect · H hr · S standup · ? help",
            title="Keybindings",
            timeout=8,
        )

    async def on_unmount(self) -> None:
        if self._client:
            await self._client.disconnect()
        await self._server.stop()
