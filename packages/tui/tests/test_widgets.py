from __future__ import annotations

import pytest
from autogenesis_tui.widgets.status_bar import StatusBar
from textual.app import App, ComposeResult


class _StatusBarApp(App):
    def compose(self) -> ComposeResult:
        yield StatusBar()


@pytest.mark.asyncio
async def test_status_bar_renders():
    async with _StatusBarApp().run_test() as pilot:
        bar = pilot.app.query_one(StatusBar)
        assert bar is not None


@pytest.mark.asyncio
async def test_status_bar_update_tokens():
    async with _StatusBarApp().run_test() as pilot:
        bar = pilot.app.query_one(StatusBar)
        bar.update_tokens(42000)
        assert bar.session_tokens == 42000


@pytest.mark.asyncio
async def test_status_bar_update_connection():
    async with _StatusBarApp().run_test() as pilot:
        bar = pilot.app.query_one(StatusBar)
        bar.update_connection("connected", "gpt-5.3-codex")
        assert bar.connection_state == "connected"
        assert bar.model_name == "gpt-5.3-codex"


from autogenesis_tui.widgets.roster import EmployeeRoster, EmployeeRow


class _RosterApp(App):
    def compose(self) -> ComposeResult:
        yield EmployeeRoster()


@pytest.mark.asyncio
async def test_roster_renders_empty():
    async with _RosterApp().run_test() as pilot:
        roster = pilot.app.query_one(EmployeeRoster)
        assert roster is not None
        assert roster.selected_employee is None


@pytest.mark.asyncio
async def test_roster_load_employees():
    rows = [
        EmployeeRow(id="backend-eng", title="Backend Engineer", status="idle"),
        EmployeeRow(id="frontend-eng", title="Frontend Engineer", status="working"),
    ]
    async with _RosterApp().run_test() as pilot:
        roster = pilot.app.query_one(EmployeeRoster)
        roster.load(rows)
        assert len(roster.rows) == 2


@pytest.mark.asyncio
async def test_roster_select_employee():
    rows = [EmployeeRow(id="backend-eng", title="Backend Engineer", status="idle")]
    selected = []

    class _TestApp(App):
        def compose(self) -> ComposeResult:
            yield EmployeeRoster()

        def on_employee_roster_selected(self, event: EmployeeRoster.Selected) -> None:
            selected.append(event.employee_id)

    async with _TestApp().run_test() as pilot:
        roster = pilot.app.query_one(EmployeeRoster)
        roster.load(rows)
        roster.select("backend-eng")
        await pilot.pause()

    assert selected == ["backend-eng"]


@pytest.mark.asyncio
async def test_roster_set_status():
    rows = [EmployeeRow(id="backend-eng", title="Backend Engineer", status="idle")]
    async with _RosterApp().run_test() as pilot:
        roster = pilot.app.query_one(EmployeeRoster)
        roster.load(rows)
        roster.set_status("backend-eng", "working")
        assert roster.rows[0].status == "working"


from autogenesis_tui.widgets.stream import AgentStream


class _StreamApp(App):
    def compose(self) -> ComposeResult:
        yield AgentStream()


@pytest.mark.asyncio
async def test_stream_renders_empty():
    async with _StreamApp().run_test() as pilot:
        stream = pilot.app.query_one(AgentStream)
        assert stream is not None
        assert stream.active_filter is None


@pytest.mark.asyncio
async def test_stream_add_agent_delta():
    async with _StreamApp().run_test() as pilot:
        stream = pilot.app.query_one(AgentStream)
        stream.add_agent_delta("Hello ", "CEO", "t-1")
        stream.add_agent_delta("world", "CEO", "t-1")
        assert len(stream.entries) == 1
        assert stream.entries[0].text == "Hello world"
        assert stream.entries[0].source == "CEO"


@pytest.mark.asyncio
async def test_stream_add_tool_block():
    async with _StreamApp().run_test() as pilot:
        stream = pilot.app.query_one(AgentStream)
        stream.add_tool_block("file_write", "src/main.py", success=True, source="backend-eng")
        assert len(stream.entries) == 1
        assert stream.entries[0].is_tool


@pytest.mark.asyncio
async def test_stream_filter_by_employee():
    async with _StreamApp().run_test() as pilot:
        stream = pilot.app.query_one(AgentStream)
        stream.add_agent_delta("CEO says hi", "CEO", "t-1")
        stream.add_agent_delta("eng says hi", "backend-eng", "t-2")
        stream.set_filter("CEO")
        visible = [e for e in stream.entries if stream._entry_visible(e)]
        assert all(e.source == "CEO" for e in visible)


from autogenesis_tui.widgets.right_panel import GoalEntry, RightPanel


class _RightPanelApp(App):
    def compose(self) -> ComposeResult:
        yield RightPanel()


@pytest.mark.asyncio
async def test_right_panel_default_mode():
    async with _RightPanelApp().run_test() as pilot:
        panel = pilot.app.query_one(RightPanel)
        assert panel.mode == "goals"


@pytest.mark.asyncio
async def test_right_panel_show_goals():
    async with _RightPanelApp().run_test() as pilot:
        panel = pilot.app.query_one(RightPanel)
        panel.update_goals([
            GoalEntry(id="g1", description="Add JWT auth", completed=2, total=4),
        ])
        assert len(panel.goals) == 1


@pytest.mark.asyncio
async def test_right_panel_update_tokens():
    async with _RightPanelApp().run_test() as pilot:
        panel = pilot.app.query_one(RightPanel)
        panel.update_tokens(session=42000, daily=100000)
        assert panel.session_tokens == 42000


@pytest.mark.asyncio
async def test_right_panel_employee_detail_mode():
    async with _RightPanelApp().run_test() as pilot:
        panel = pilot.app.query_one(RightPanel)
        panel.show_employee(
            employee_id="backend-eng",
            memories=["Prefers asyncio", "Uses pytest"],
            inbox_count=3,
            training=["Always use type hints"],
        )
        assert panel.mode == "employee"
        assert panel.focused_employee == "backend-eng"


@pytest.mark.asyncio
async def test_right_panel_back_to_goals():
    async with _RightPanelApp().run_test() as pilot:
        panel = pilot.app.query_one(RightPanel)
        panel.show_employee("backend-eng", [], 0, [])
        panel.show_goals()
        assert panel.mode == "goals"


from autogenesis_tui.widgets.input_bar import InputBar


class _InputBarApp(App):
    submitted: list[tuple[str, str]] = []

    def compose(self) -> ComposeResult:
        yield InputBar()

    def on_input_bar_submitted(self, event: InputBar.Submitted) -> None:
        _InputBarApp.submitted.append((event.target, event.text))


@pytest.mark.asyncio
async def test_input_bar_renders():
    async with _InputBarApp().run_test() as pilot:
        bar = pilot.app.query_one(InputBar)
        assert bar is not None
        assert bar.target == "CEO"


@pytest.mark.asyncio
async def test_input_bar_set_target():
    async with _InputBarApp().run_test() as pilot:
        bar = pilot.app.query_one(InputBar)
        bar.set_target("backend-eng")
        assert bar.target == "backend-eng"


@pytest.mark.asyncio
async def test_input_bar_load_targets():
    async with _InputBarApp().run_test() as pilot:
        bar = pilot.app.query_one(InputBar)
        bar.load_targets(["CEO", "backend-eng", "frontend-eng"])
        assert "backend-eng" in bar.targets
