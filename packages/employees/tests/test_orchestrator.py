"""Tests for CEOOrchestrator — the core run loop with mocked dependencies."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from autogenesis_employees.orchestrator import CEOOrchestrator


class TestStripCodexBoilerplate:
    def test_strips_banner_and_echo(self):
        raw = (
            "OpenAI Codex v0.114.0 (research preview)\n"
            "--------\n"
            "workdir: /home/user/projects/AutoGenesis\n"
            "user\n"
            'Respond with JSON: [{"description": "..."}]\n'
            "mcp: excel ready\n"
            "codex\n"
            '[{"description": "Build the API", "rationale": "needed"}]\n'
            "tokens used\n"
            "5000\n"
        )
        result = CEOOrchestrator._strip_codex_boilerplate(raw)
        assert result.startswith('[{"description": "Build the API"')
        assert "OpenAI Codex" not in result
        assert "user" not in result

    def test_no_marker_returns_full_output(self):
        raw = '{"employee_id": "cto"}'
        assert CEOOrchestrator._strip_codex_boilerplate(raw) == raw

    def test_uses_last_marker(self):
        raw = "codex\nfirst response\ncodex\nsecond response\n"
        result = CEOOrchestrator._strip_codex_boilerplate(raw)
        assert result == "second response\n"


def _mock_spawn_success(output: str = "Done"):
    result = MagicMock()
    result.output = output
    result.exit_code = 0
    result.timed_out = False
    result.success = True
    return result


def _mock_spawn_failure(output: str = "Error occurred"):
    result = MagicMock()
    result.output = output
    result.exit_code = 1
    result.timed_out = False
    result.success = False
    return result


@pytest.fixture
def mock_deps(tmp_path):
    registry = MagicMock()
    emp = MagicMock()
    emp.id = "backend-engineer"
    emp.title = "Backend Engineer"
    emp.persona = "Writes APIs"
    emp.tools = ["shell"]
    emp.training_directives = []
    emp.env = {}
    registry.list_active.return_value = [emp]
    registry.get.return_value = emp

    runtime = MagicMock()
    runtime.build_system_prompt.return_value = "You are Backend Engineer..."

    sub_agent_mgr = MagicMock()
    sub_agent_mgr.spawn = AsyncMock(return_value=_mock_spawn_success())

    # codex is still accepted by CEOOrchestrator.__init__ but no longer used
    codex = MagicMock()

    return {
        "registry": registry,
        "runtime": runtime,
        "sub_agent_mgr": sub_agent_mgr,
        "codex": codex,
        "base_dir": tmp_path / ".autogenesis",
    }


class TestCEOOrchestrator:
    async def test_enqueue_and_status(self, mock_deps):
        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        task_id = await orch.enqueue("Fix login bug", priority=5)
        assert task_id is not None
        items = await orch.status()
        assert len(items) >= 1
        await orch.close()

    async def test_run_single_subtask_goal(self, mock_deps):
        sub = mock_deps["sub_agent_mgr"]
        decompose_json = json.dumps(
            [{"description": "Build the endpoint", "rationale": "Only task"}]
        )
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best fit"})

        # Single subtask: decompose → assign → dispatch (no re-evaluate, remaining is empty)
        sub.spawn = AsyncMock(
            side_effect=[
                _mock_spawn_success(decompose_json),  # 1. decompose
                _mock_spawn_success(assign_json),  # 2. assign
                _mock_spawn_success("Done"),  # 3. employee dispatch
            ]
        )

        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        result = await orch.run("Build user auth")
        assert result.status == "completed"
        assert len(result.subtask_results) == 1
        assert result.subtask_results[0].employee_id == "backend-engineer"
        await orch.close()

    async def test_run_with_retry_on_failure(self, mock_deps):
        sub = mock_deps["sub_agent_mgr"]

        decompose_json = json.dumps([{"description": "Build API"}])
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best"})

        # Single subtask: decompose → assign → dispatch-fail → dispatch-retry-ok
        # No re-evaluate since remaining is empty after the one subtask
        sub.spawn = AsyncMock(
            side_effect=[
                _mock_spawn_success(decompose_json),  # 1. decompose
                _mock_spawn_success(assign_json),  # 2. assign
                _mock_spawn_failure(),  # 3. dispatch (fail)
                _mock_spawn_success("Done"),  # 4. dispatch retry (success)
            ]
        )

        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        result = await orch.run("Build API")
        assert result.status == "completed"
        # spawn called 4 times: decompose + assign + fail + retry
        assert sub.spawn.call_count == 4
        await orch.close()

    async def test_run_escalation_after_two_failures(self, mock_deps):
        sub = mock_deps["sub_agent_mgr"]

        decompose_json = json.dumps([{"description": "Build API"}])
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best"})

        # decompose → assign → dispatch-fail → dispatch-retry-fail → escalated
        sub.spawn = AsyncMock(
            side_effect=[
                _mock_spawn_success(decompose_json),  # 1. decompose
                _mock_spawn_success(assign_json),  # 2. assign
                _mock_spawn_failure(),  # 3. dispatch (fail)
                _mock_spawn_failure(),  # 4. dispatch retry (fail) → escalate
            ]
        )

        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        result = await orch.run("Build API")
        assert result.status == "escalated"
        assert sub.spawn.call_count == 4
        await orch.close()

    async def test_dispatch_standalone_task(self, mock_deps):
        sub = mock_deps["sub_agent_mgr"]
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best"})

        # dispatch(): assign (reasoning spawn) → employee dispatch (spawn)
        sub.spawn = AsyncMock(
            side_effect=[
                _mock_spawn_success(assign_json),  # 1. assign
                _mock_spawn_success("Done"),  # 2. employee dispatch
            ]
        )

        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        task_id = await orch.enqueue("Fix bug")
        result = await orch.dispatch(task_id)
        assert result.status == "completed"
        assert result.employee_id == "backend-engineer"
        await orch.close()

    async def test_dispatch_next_from_queue(self, mock_deps):
        sub = mock_deps["sub_agent_mgr"]
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best"})

        sub.spawn = AsyncMock(
            side_effect=[
                _mock_spawn_success(assign_json),  # 1. assign (picks highest priority)
                _mock_spawn_success("Done"),  # 2. employee dispatch
            ]
        )

        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        await orch.enqueue("Low priority", priority=1)
        await orch.enqueue("High priority", priority=10)
        result = await orch.dispatch()
        assert result.task_id is not None
        await orch.close()

    async def test_empty_roster_raises(self, mock_deps):
        mock_deps["registry"].list_active.return_value = []
        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        with pytest.raises(RuntimeError, match="No active employees"):
            await orch.run("Build something")
        await orch.close()

    async def test_resume_continues_from_escalated(self, mock_deps):
        sub = mock_deps["sub_agent_mgr"]

        decompose_json = json.dumps([{"description": "Step 1"}, {"description": "Step 2"}])
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best"})
        reevaluate_json = json.dumps({"no_changes": True})

        # First run (2 subtasks):
        # decompose → assign-st1 → dispatch-st1-ok → reevaluate (remaining has st2)
        # → assign-st2 → dispatch-st2-fail → dispatch-st2-retry-fail → escalated
        sub.spawn = AsyncMock(
            side_effect=[
                _mock_spawn_success(decompose_json),  # 1. decompose
                _mock_spawn_success(assign_json),  # 2. assign st1
                _mock_spawn_success("Done"),  # 3. dispatch st1 (success)
                _mock_spawn_success(reevaluate_json),  # 4. re-evaluate (st2 still pending)
                _mock_spawn_success(assign_json),  # 5. assign st2
                _mock_spawn_failure(),  # 6. dispatch st2 (fail)
                _mock_spawn_failure(),  # 7. dispatch st2 retry (fail) → escalate
            ]
        )

        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        result = await orch.run("Two steps")
        assert result.status == "escalated"
        goal_id = result.goal_id

        # Resume: assign-st2 → dispatch-st2-ok (no re-evaluate, remaining empty)
        sub.spawn = AsyncMock(
            side_effect=[
                _mock_spawn_success(assign_json),  # 1. assign st2
                _mock_spawn_success("Done"),  # 2. dispatch st2 (success)
            ]
        )
        resumed = await orch.resume(goal_id)
        assert resumed.status == "completed"
        assert resumed.goal_id == goal_id
        await orch.close()

    async def test_plan_markdown_created(self, mock_deps):
        sub = mock_deps["sub_agent_mgr"]
        decompose_json = json.dumps([{"description": "Step 1"}, {"description": "Step 2"}])
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best"})
        reevaluate_json = json.dumps({"no_changes": True})

        # 2 subtasks:
        # decompose → assign-st1 → dispatch-st1-ok → reevaluate
        # → assign-st2 → dispatch-st2-ok (no reevaluate, remaining empty)
        sub.spawn = AsyncMock(
            side_effect=[
                _mock_spawn_success(decompose_json),  # 1. decompose
                _mock_spawn_success(assign_json),  # 2. assign st1
                _mock_spawn_success("Done"),  # 3. dispatch st1
                _mock_spawn_success(reevaluate_json),  # 4. re-evaluate
                _mock_spawn_success(assign_json),  # 5. assign st2
                _mock_spawn_success("Done"),  # 6. dispatch st2
            ]
        )

        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        result = await orch.run("Two step goal")
        plan_path = Path(result.plan_path)
        assert plan_path.exists()
        content = plan_path.read_text()
        assert "Step 1" in content
        assert "Step 2" in content
        # Both subtasks should be checked off
        assert content.count("- [x]") == 2
        await orch.close()
