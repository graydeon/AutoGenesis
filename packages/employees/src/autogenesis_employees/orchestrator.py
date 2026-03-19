"""CEOOrchestrator — the central brain of the agent employee system.

Decomposes goals into subtasks, assigns employees via LLM reasoning,
dispatches via SubAgentManager, and adapts plans based on results.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog
from autogenesis_core.events import Event, EventType, get_event_bus

from autogenesis_employees.ceo_models import (
    GoalResult,
    GoalStatus,
    ManagerBundle,
    SubtaskResult,
    TaskResult,
    TaskStatus,
)
from autogenesis_employees.reasoning import (
    build_assign_prompt,
    build_decompose_prompt,
    build_reevaluate_prompt,
    extract_json,
)
from autogenesis_employees.state import CEOStateManager

if TYPE_CHECKING:
    from autogenesis_core.client import CodexClient
    from autogenesis_core.sub_agents import SubAgentManager

    from autogenesis_employees.changelog import ChangelogManager
    from autogenesis_employees.registry import EmployeeRegistry
    from autogenesis_employees.runtime import EmployeeRuntime

logger = structlog.get_logger()


def _find_project_root() -> Path:
    """Walk up from cwd looking for .autogenesis/ directory."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".autogenesis").is_dir():
            return parent
    return cwd


class CEOOrchestrator:
    """Coordinates employee dispatch for goals and standalone tasks."""

    def __init__(  # noqa: PLR0913
        self,
        registry: EmployeeRegistry,
        runtime: EmployeeRuntime,
        sub_agent_mgr: SubAgentManager,
        codex: CodexClient,
        base_dir: Path | None = None,
        dispatch_timeout: float = 300.0,
    ) -> None:
        self._registry = registry
        self._runtime = runtime
        self._sub_agent_mgr = sub_agent_mgr
        self._codex = codex
        self._dispatch_timeout = dispatch_timeout
        self._project_root = _find_project_root()
        self._base_dir = base_dir or (self._project_root / ".autogenesis")
        self._state: CEOStateManager | None = None
        self._changelog: ChangelogManager | None = None
        self._managers: dict[str, ManagerBundle] = {}
        self._bus = get_event_bus()

    async def initialize(self) -> None:
        """Initialize state DB and changelog."""
        from autogenesis_employees.changelog import ChangelogManager

        ceo_dir = self._base_dir / "ceo"
        ceo_dir.mkdir(parents=True, exist_ok=True)
        (ceo_dir / "plans").mkdir(exist_ok=True)

        self._state = CEOStateManager(db_path=ceo_dir / "ceo.db")
        await self._state.initialize()

        self._changelog = ChangelogManager(self._base_dir / "changelog.md")

    async def close(self) -> None:
        """Close all manager connections and state DB."""
        for bundle in self._managers.values():
            await bundle.brain.close()
            await bundle.inbox.close()
        self._managers.clear()
        if self._state:
            await self._state.close()

    def _require_state(self) -> CEOStateManager:
        if self._state is None:
            msg = "CEOOrchestrator not initialized"
            raise RuntimeError(msg)
        return self._state

    # --- Manager lifecycle ---

    async def _get_managers(self, employee_id: str) -> ManagerBundle:
        if employee_id not in self._managers:
            from autogenesis_employees.brain import BrainManager
            from autogenesis_employees.inbox import InboxManager

            data_dir = self._base_dir / "employees" / employee_id
            brain = BrainManager(data_dir / "brain.db")
            inbox = InboxManager(data_dir / "inbox.db")
            await brain.initialize()
            await inbox.initialize()
            self._managers[employee_id] = ManagerBundle(brain=brain, inbox=inbox)
        return self._managers[employee_id]

    # --- Roster helpers ---

    def _check_roster(self) -> None:
        if not self._registry.list_active():
            msg = "No active employees — use `autogenesis hr hire` to add employees"
            raise RuntimeError(msg)

    def _roster_summary(self) -> list[dict[str, Any]]:
        return [
            {
                "id": e.id,
                "title": e.title,
                "persona": e.persona,
                "tools": e.tools,
                "training_directives": e.training_directives,
            }
            for e in self._registry.list_active()
        ]

    # --- LLM calls ---

    async def _codex_call(
        self, instructions: str, user_message: str, label: str = "ceo-reasoning"
    ) -> str:
        """Make a reasoning call via codex exec subprocess."""
        prompt = f"{instructions}\n\n{user_message}"
        result = await self._sub_agent_mgr.spawn(
            task=prompt,
            cwd=str(self._project_root),
            timeout=self._dispatch_timeout,
            system_prompt=instructions,
            label=label,
        )
        return result.output

    async def _codex_call_json(
        self, instructions: str, user_message: str, label: str = "ceo-reasoning"
    ) -> Any:  # noqa: ANN401
        """Make a reasoning call and extract JSON. Retries once on parse failure."""
        text = await self._codex_call(instructions, user_message, label=label)
        try:
            return extract_json(text)
        except ValueError:
            retry_instructions = (
                instructions + "\n\nIMPORTANT: Respond with ONLY valid JSON. No other text."
            )
            text = await self._codex_call(retry_instructions, user_message)
            return extract_json(text)

    # --- Context building ---

    async def _build_employee_context(self, employee_id: str, task: str) -> str:
        """Build system prompt for an employee dispatch."""
        config = self._registry.get(employee_id)
        if not config:
            msg = f"Employee {employee_id} not found"
            raise RuntimeError(msg)

        managers = await self._get_managers(employee_id)
        brain_context = [m.content for m in await managers.brain.top_memories(20)]
        inbox_messages = [
            f"From {m.from_employee}: {m.subject}\n{m.body}"
            for m in await managers.inbox.get_unread(employee_id)
        ]
        changelog_entries = self._changelog.read_recent(10) if self._changelog else []

        return self._runtime.build_system_prompt(
            config=config,
            brain_context=brain_context,
            inbox_messages=inbox_messages,
            changelog_entries=changelog_entries,
            task=task,
        )

    # --- Plan markdown ---

    def _write_plan(self, goal_id: str, goal: str, subtasks: list[dict[str, Any]]) -> Path:
        """Write initial plan markdown."""
        plan_path = self._base_dir / "ceo" / "plans" / f"goal-{goal_id}.md"
        lines = [f"# Goal: {goal}\n", "Status: executing\n", "\n## Subtasks\n"]
        for i, st in enumerate(subtasks, 1):
            lines.append(f"- [ ] **{i}. {st['description']}**\n  (pending)\n")
        plan_path.write_text("\n".join(lines))
        return plan_path

    def _update_plan_subtask(
        self, plan_path: Path, index: int, employee_id: str, result_summary: str
    ) -> None:
        """Mark a subtask as complete in the plan markdown."""
        content = plan_path.read_text()
        count = 0
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.strip().startswith(("- [ ] **", "- [x] **")):
                count += 1
                if count == index and line.strip().startswith("- [ ] **"):
                    lines[i] = line.replace("- [ ]", "- [x]")
                    if i + 1 < len(lines) and "(pending)" in lines[i + 1]:
                        lines[i + 1] = f"  Assigned to: {employee_id}\n  Result: {result_summary}"
                    break
        plan_path.write_text("\n".join(lines))

    def _update_plan_status(self, plan_path: Path, status: str) -> None:
        content = plan_path.read_text()
        content = content.replace("Status: executing", f"Status: {status}")
        plan_path.write_text(content)

    def _rewrite_remaining_subtasks(
        self, plan_path: Path, completed_count: int, new_subtasks: list[dict[str, Any]]
    ) -> None:
        """Replace remaining subtasks in plan after re-evaluation."""
        content = plan_path.read_text()
        lines = content.split("\n")
        result_lines: list[str] = []
        for line in lines:
            if line.strip().startswith("- [ ] **"):
                break
            result_lines.append(line)

        for i, st in enumerate(new_subtasks, completed_count + 1):
            result_lines.append(f"- [ ] **{i}. {st['description']}**\n  (pending)\n")

        plan_path.write_text("\n".join(result_lines))

    # --- Dispatch ---

    async def _dispatch_employee(
        self,
        employee_id: str,
        task: str,
        failure_context: str | None = None,
    ) -> tuple[str, int, bool]:
        """Dispatch a single employee. Returns (output, exit_code, success)."""
        if failure_context:
            task_with_context = (
                f"{task}\n\n## Previous Attempt Failed\n\n{failure_context}\n"
                "Analyze what went wrong and try a different approach."
            )
        else:
            task_with_context = task

        system_prompt = await self._build_employee_context(employee_id, task_with_context)
        config = self._registry.get(employee_id)
        env_overrides = config.env if config else {}

        result = await self._sub_agent_mgr.spawn(
            task=task_with_context,
            cwd=str(self._project_root),
            timeout=self._dispatch_timeout,
            system_prompt=system_prompt,
            env_overrides=env_overrides,
            label=employee_id,
        )
        return result.output, result.exit_code, result.success

    # --- Public API ---

    async def enqueue(self, description: str, priority: int = 0) -> str:
        """Push a task onto the queue. Returns task ID."""
        state = self._require_state()
        return await state.create_task(description, priority=priority)

    async def run(self, goal: str) -> GoalResult:
        """Decompose and execute a high-level goal."""
        state = self._require_state()
        self._check_roster()

        self._bus.emit(Event(event_type=EventType.CEO_GOAL_START, data={"goal": goal}))
        logger.info("ceo_goal_start", goal=goal[:100])

        # 1. Decompose
        roster = self._roster_summary()
        changelog = self._changelog.read_recent(5) if self._changelog else []
        instructions, message = build_decompose_prompt(goal, roster, changelog)
        subtasks_raw = await self._codex_call_json(instructions, message, label="ceo:decompose")
        if not isinstance(subtasks_raw, list) or not subtasks_raw:
            msg = "Decompose returned empty or invalid subtasks"
            raise RuntimeError(msg)

        # 2. Create goal record first, then write plan with real ID
        goal_id = await state.create_goal(goal, plan_path="")
        plan_path = self._write_plan(goal_id, goal, subtasks_raw)
        await state.update_goal_plan_path(goal_id, str(plan_path))
        await state.update_goal(goal_id, status="executing")

        # 3. Execute via rolling dispatch
        return await self._execute_plan(
            goal_id=goal_id,
            goal=goal,
            plan_path=plan_path,
            remaining=list(subtasks_raw),
            completed_count=0,
        )

    async def _execute_plan(  # noqa: PLR0915
        self,
        goal_id: str,
        goal: str,
        plan_path: Path,
        remaining: list[dict[str, Any]],
        completed_count: int,
    ) -> GoalResult:
        """Run the rolling dispatch loop — shared by run() and resume()."""
        state = self._require_state()
        roster = self._roster_summary()
        subtask_results: list[SubtaskResult] = []

        # Gather previous results from executions table (for resume)
        prev_execs = await state.list_executions(goal_id=goal_id)
        previous_results = [
            {"subtask": e["subtask"], "result": (e.get("output") or "")[:200]}
            for e in prev_execs
            if e["status"] == "completed"
        ]

        while remaining:
            current = remaining.pop(0)
            subtask_desc = current["description"]
            completed_count += 1

            # Assign
            instructions, message = build_assign_prompt(
                subtask=subtask_desc,
                goal_context=goal,
                roster_details=roster,
                previous_results=previous_results,
            )
            assign_result = await self._codex_call_json(instructions, message, label="ceo:assign")
            employee_id = assign_result.get("employee_id", "")
            if not self._registry.get(employee_id):
                employee_id = self._registry.list_active()[0].id

            self._bus.emit(
                Event(
                    event_type=EventType.CEO_SUBTASK_ASSIGN,
                    data={"subtask": subtask_desc, "employee_id": employee_id},
                )
            )
            logger.info("ceo_subtask_assign", subtask=subtask_desc[:80], employee=employee_id)

            # Dispatch with retry
            start_time = time.monotonic()
            output, _exit_code, success = await self._dispatch_employee(employee_id, subtask_desc)
            attempt = 1

            exec_id = await state.record_execution(
                goal_id=goal_id,
                task_id=None,
                subtask=subtask_desc,
                employee_id=employee_id,
                attempt=attempt,
            )

            if not success:
                logger.warning("ceo_subtask_fail_retry", subtask=subtask_desc[:80], attempt=1)
                await state.update_execution(exec_id, status="failed", output=output)
                attempt = 2
                output, _exit_code, success = await self._dispatch_employee(
                    employee_id, subtask_desc, failure_context=output
                )
                exec_id = await state.record_execution(
                    goal_id=goal_id,
                    task_id=None,
                    subtask=subtask_desc,
                    employee_id=employee_id,
                    attempt=attempt,
                )

            duration = time.monotonic() - start_time

            if success:
                await state.update_execution(exec_id, status="completed", output=output)
                self._update_plan_subtask(plan_path, completed_count, employee_id, output[:200])
                self._bus.emit(
                    Event(
                        event_type=EventType.CEO_SUBTASK_COMPLETE,
                        data={"subtask": subtask_desc, "employee_id": employee_id},
                    )
                )
                subtask_results.append(
                    SubtaskResult(
                        subtask=subtask_desc,
                        employee_id=employee_id,
                        status="completed",
                        output=output,
                        attempt=attempt,
                        duration_seconds=duration,
                    )
                )
                previous_results.append({"subtask": subtask_desc, "result": output[:200]})

                # Re-evaluate if more subtasks remain
                if remaining:
                    plan_text = plan_path.read_text()
                    instructions, message = build_reevaluate_prompt(goal, plan_text, output[:500])
                    reeval = await self._codex_call_json(
                        instructions, message, label="ceo:re-evaluate"
                    )
                    if isinstance(reeval, list):
                        remaining = reeval
                        self._rewrite_remaining_subtasks(plan_path, completed_count, remaining)
            else:
                await state.update_execution(exec_id, status="failed", output=output)
                self._bus.emit(
                    Event(
                        event_type=EventType.CEO_SUBTASK_FAIL,
                        data={
                            "subtask": subtask_desc,
                            "employee_id": employee_id,
                            "output": output[:500],
                        },
                    )
                )
                self._bus.emit(
                    Event(
                        event_type=EventType.CEO_ESCALATION,
                        data={
                            "goal_id": goal_id,
                            "subtask": subtask_desc,
                            "output": output[:500],
                        },
                    )
                )
                subtask_results.append(
                    SubtaskResult(
                        subtask=subtask_desc,
                        employee_id=employee_id,
                        status="escalated",
                        output=output,
                        attempt=attempt,
                        duration_seconds=duration,
                    )
                )
                await state.update_goal(goal_id, status="escalated")
                self._update_plan_status(plan_path, "escalated")
                logger.error("ceo_escalation", goal_id=goal_id, subtask=subtask_desc[:80])
                return GoalResult(
                    goal_id=goal_id,
                    status="escalated",
                    subtask_results=subtask_results,
                    plan_path=str(plan_path),
                )

        # All subtasks complete
        await state.update_goal(goal_id, status="completed")
        self._update_plan_status(plan_path, "completed")
        self._bus.emit(Event(event_type=EventType.CEO_GOAL_COMPLETE, data={"goal_id": goal_id}))
        logger.info("ceo_goal_complete", goal_id=goal_id)

        return GoalResult(
            goal_id=goal_id,
            status="completed",
            subtask_results=subtask_results,
            plan_path=str(plan_path),
        )

    async def dispatch(self, task_id: str | None = None) -> TaskResult:
        """Execute a standalone task from the queue."""
        state = self._require_state()
        self._check_roster()

        if task_id:
            task = await state.get_task(task_id)
        else:
            pending = await state.list_pending_tasks()
            if not pending:
                msg = "No pending tasks in queue"
                raise RuntimeError(msg)
            task = pending[0]
            task_id = task["id"]

        if not task:
            msg = f"Task {task_id} not found"
            raise RuntimeError(msg)

        await state.update_task(task_id, status="in_progress")

        # Assign
        roster = self._roster_summary()
        instructions, message = build_assign_prompt(
            subtask=task["description"],
            goal_context=task["description"],
            roster_details=roster,
            previous_results=[],
        )
        assign_result = await self._codex_call_json(instructions, message)
        employee_id = assign_result.get("employee_id", "")
        if not self._registry.get(employee_id):
            employee_id = self._registry.list_active()[0].id

        # Dispatch
        start_time = time.monotonic()
        output, _exit_code, success = await self._dispatch_employee(
            employee_id, task["description"]
        )
        attempt = 1

        exec_id = await state.record_execution(
            goal_id=None,
            task_id=task_id,
            subtask=task["description"],
            employee_id=employee_id,
            attempt=attempt,
        )

        if not success:
            await state.update_execution(exec_id, status="failed", output=output)
            attempt = 2
            output, _exit_code, success = await self._dispatch_employee(
                employee_id, task["description"], failure_context=output
            )
            exec_id = await state.record_execution(
                goal_id=None,
                task_id=task_id,
                subtask=task["description"],
                employee_id=employee_id,
                attempt=attempt,
            )

        duration = time.monotonic() - start_time

        if success:
            await state.update_execution(exec_id, status="completed", output=output)
            await state.update_task(task_id, status="completed", result=output[:500])
            return TaskResult(
                task_id=task_id,
                status="completed",
                employee_id=employee_id,
                output=output,
                duration_seconds=duration,
            )

        await state.update_execution(exec_id, status="failed", output=output)
        await state.update_task(task_id, status="escalated", result=output[:500])
        return TaskResult(
            task_id=task_id,
            status="escalated",
            employee_id=employee_id,
            output=output,
            duration_seconds=duration,
        )

    async def resume(self, goal_id: str) -> GoalResult:
        """Resume an escalated goal from last incomplete subtask."""
        state = self._require_state()
        self._check_roster()
        goal = await state.get_goal(goal_id)
        if not goal:
            msg = f"Goal {goal_id} not found"
            raise RuntimeError(msg)

        plan_path = Path(goal["plan_path"])
        if not plan_path.exists():
            msg = f"Plan file not found: {plan_path}"
            raise RuntimeError(msg)

        remaining = self._parse_remaining_subtasks(plan_path)
        if not remaining:
            msg = "No remaining subtasks to resume"
            raise RuntimeError(msg)

        await state.update_goal(goal_id, status="executing")
        return await self._execute_plan(
            goal_id=goal_id,
            goal=goal["description"],
            plan_path=plan_path,
            remaining=remaining,
            completed_count=self._count_completed_subtasks(plan_path),
        )

    def _parse_remaining_subtasks(self, plan_path: Path) -> list[dict[str, Any]]:
        """Parse unchecked subtasks from plan markdown."""
        content = plan_path.read_text()
        return [
            {"description": match.group(1).strip()}
            for match in re.finditer(r"- \[ \] \*\*\d+\.\s+(.+?)\*\*", content)
        ]

    def _count_completed_subtasks(self, plan_path: Path) -> int:
        """Count checked subtasks in plan markdown."""
        content = plan_path.read_text()
        return len(re.findall(r"- \[x\] \*\*", content))

    def _count_total_subtasks(self, plan_path: Path) -> int:
        """Count all subtasks (checked + unchecked) in plan markdown."""
        content = plan_path.read_text()
        return len(re.findall(r"- \[[ x]\] \*\*", content))

    async def status(self) -> list[GoalStatus | TaskStatus]:
        """Return current state of all goals and tasks."""
        state = self._require_state()
        items = await state.list_all_status()
        result: list[GoalStatus | TaskStatus] = []
        for item in items:
            if item.get("type") == "goal":
                plan_p = Path(item.get("plan_path", ""))
                total = self._count_total_subtasks(plan_p) if plan_p.exists() else 0
                completed = self._count_completed_subtasks(plan_p) if plan_p.exists() else 0
                result.append(
                    GoalStatus(
                        goal_id=item["id"],
                        description=item["description"],
                        status=item["status"],
                        subtasks_completed=completed,
                        subtasks_total=total,
                        plan_path=item.get("plan_path", ""),
                    )
                )
            else:
                result.append(
                    TaskStatus(
                        task_id=item["id"],
                        description=item["description"],
                        status=item["status"],
                        priority=item.get("priority", 0),
                    )
                )
        return result
