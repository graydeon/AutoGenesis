"""Tests for CEOOrchestrator — the core run loop with mocked dependencies."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from autogenesis_employees.orchestrator import CEOOrchestrator


def _mock_codex_result(text: str):
    result = MagicMock()
    result.text = text
    return result


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

    codex = MagicMock()
    codex.create_response_sync = AsyncMock()

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
        codex = mock_deps["codex"]
        decompose_json = json.dumps(
            [{"description": "Build the endpoint", "rationale": "Only task"}]
        )
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best fit"})
        reevaluate_json = json.dumps({"no_changes": True})

        codex.create_response_sync = AsyncMock(
            side_effect=[
                _mock_codex_result(decompose_json),
                _mock_codex_result(assign_json),
                _mock_codex_result(reevaluate_json),
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
        codex = mock_deps["codex"]
        sub = mock_deps["sub_agent_mgr"]

        decompose_json = json.dumps([{"description": "Build API"}])
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best"})
        reevaluate_json = json.dumps({"no_changes": True})

        codex.create_response_sync = AsyncMock(
            side_effect=[
                _mock_codex_result(decompose_json),
                _mock_codex_result(assign_json),
                _mock_codex_result(reevaluate_json),
            ]
        )
        sub.spawn = AsyncMock(side_effect=[_mock_spawn_failure(), _mock_spawn_success()])

        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        result = await orch.run("Build API")
        assert result.status == "completed"
        assert sub.spawn.call_count == 2
        await orch.close()

    async def test_run_escalation_after_two_failures(self, mock_deps):
        codex = mock_deps["codex"]
        sub = mock_deps["sub_agent_mgr"]

        decompose_json = json.dumps([{"description": "Build API"}])
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best"})

        codex.create_response_sync = AsyncMock(
            side_effect=[
                _mock_codex_result(decompose_json),
                _mock_codex_result(assign_json),
            ]
        )
        sub.spawn = AsyncMock(return_value=_mock_spawn_failure())

        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        result = await orch.run("Build API")
        assert result.status == "escalated"
        assert sub.spawn.call_count == 2
        await orch.close()

    async def test_dispatch_standalone_task(self, mock_deps):
        codex = mock_deps["codex"]
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best"})
        codex.create_response_sync = AsyncMock(return_value=_mock_codex_result(assign_json))

        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        task_id = await orch.enqueue("Fix bug")
        result = await orch.dispatch(task_id)
        assert result.status == "completed"
        assert result.employee_id == "backend-engineer"
        await orch.close()

    async def test_dispatch_next_from_queue(self, mock_deps):
        codex = mock_deps["codex"]
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best"})
        codex.create_response_sync = AsyncMock(return_value=_mock_codex_result(assign_json))

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
        codex = mock_deps["codex"]
        sub = mock_deps["sub_agent_mgr"]

        decompose_json = json.dumps([{"description": "Step 1"}, {"description": "Step 2"}])
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best"})
        reevaluate_json = json.dumps({"no_changes": True})

        codex.create_response_sync = AsyncMock(
            side_effect=[
                _mock_codex_result(decompose_json),
                _mock_codex_result(assign_json),
                _mock_codex_result(reevaluate_json),
                _mock_codex_result(assign_json),
            ]
        )
        sub.spawn = AsyncMock(
            side_effect=[_mock_spawn_success(), _mock_spawn_failure(), _mock_spawn_failure()]
        )

        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        result = await orch.run("Two steps")
        assert result.status == "escalated"
        goal_id = result.goal_id

        codex.create_response_sync = AsyncMock(
            side_effect=[
                _mock_codex_result(assign_json),
                _mock_codex_result(reevaluate_json),
            ]
        )
        sub.spawn = AsyncMock(return_value=_mock_spawn_success())
        resumed = await orch.resume(goal_id)
        assert resumed.status == "completed"
        assert resumed.goal_id == goal_id
        await orch.close()

    async def test_plan_markdown_created(self, mock_deps):
        codex = mock_deps["codex"]
        decompose_json = json.dumps([{"description": "Step 1"}, {"description": "Step 2"}])
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best"})
        reevaluate_json = json.dumps({"no_changes": True})

        codex.create_response_sync = AsyncMock(
            side_effect=[
                _mock_codex_result(decompose_json),
                _mock_codex_result(assign_json),
                _mock_codex_result(reevaluate_json),
                _mock_codex_result(assign_json),
                _mock_codex_result(reevaluate_json),
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
        await orch.close()
