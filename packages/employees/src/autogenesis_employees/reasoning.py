"""CEO reasoning — JSON extraction and prompt builders for Codex calls.

Three reasoning calls:
1. Decompose: goal → ordered subtasks
2. Assign: subtask → employee pick
3. Re-evaluate: completed work → updated plan

Each builder returns (instructions: str, user_message: str) to pass to
CodexClient.create_response_sync().
"""

from __future__ import annotations

import json
import re
from typing import Any

_FENCED_JSON_RE = re.compile(r"```(?:json)?\s*\n([\s\S]*?)\n```", re.MULTILINE)


def extract_json(text: str) -> object:
    """Extract first JSON array or object from text.

    Tries fenced ```json blocks first, then scans for raw JSON.
    Raises ValueError if no valid JSON found.
    """
    match = _FENCED_JSON_RE.search(text)
    if match:
        return json.loads(match.group(1).strip())

    for i, ch in enumerate(text):
        if ch in ("[", "{"):
            try:
                return json.loads(text[i:])
            except json.JSONDecodeError:
                depth = 0
                close = "]" if ch == "[" else "}"
                for j in range(i, len(text)):
                    if text[j] == ch:
                        depth += 1
                    elif text[j] == close:
                        depth -= 1
                        if depth == 0:
                            try:
                                return json.loads(text[i : j + 1])
                            except json.JSONDecodeError:
                                break
                continue

    msg = "No JSON found in text"
    raise ValueError(msg)


def build_decompose_prompt(
    goal: str,
    roster_summary: list[dict[str, Any]],
    changelog_entries: list[str],
) -> tuple[str, str]:
    """Build the decompose reasoning call. Returns (instructions, user_message)."""
    instructions = (
        "You are the CEO of a software startup. Decompose the given goal into concrete, "
        "ordered subtasks. Each subtask should be completable by one employee in one session. "
        "Consider the available team and their capabilities.\n\n"
        "Respond with ONLY a JSON array of objects: "
        '[{"description": "...", "rationale": "..."}]'
    )

    parts = [f"## Goal\n\n{goal}\n"]

    if roster_summary:
        parts.append("## Available Team\n")
        for emp in roster_summary:
            tools_str = ", ".join(emp.get("tools", []))
            title = emp["title"]
            eid = emp["id"]
            persona = emp.get("persona", "")
            parts.append(f"- **{title}** (id: {eid}): {persona}. Tools: {tools_str}")
        parts.append("")

    if changelog_entries:
        parts.append("## Recent Activity\n")
        parts.extend(changelog_entries[:5])
        parts.append("")

    return instructions, "\n".join(parts)


def build_assign_prompt(
    subtask: str,
    goal_context: str,
    roster_details: list[dict[str, Any]],
    previous_results: list[dict[str, Any]],
) -> tuple[str, str]:
    """Build the assign reasoning call. Returns (instructions, user_message)."""
    instructions = (
        "Given a subtask and available employees, pick the single best employee to handle it. "
        "Consider their tools, training, and expertise.\n\n"
        'Respond with ONLY a JSON object: {"employee_id": "...", "reasoning": "..."}'
    )

    parts = [f"## Overall Goal\n\n{goal_context}\n", f"## Current Subtask\n\n{subtask}\n"]

    if roster_details:
        parts.append("## Available Employees\n")
        for emp in roster_details:
            tools_str = ", ".join(emp.get("tools", []))
            directives = emp.get("training_directives", [])
            directives_str = "; ".join(directives) if directives else "none"
            parts.append(
                f"- **{emp.get('title', emp['id'])}** (id: {emp['id']}): "
                f"{emp.get('persona', '')}. Tools: {tools_str}. Training: {directives_str}"
            )
        parts.append("")

    if previous_results:
        parts.append("## Previous Subtask Results\n")
        parts.extend(
            f"- {prev['subtask']}: {prev.get('result', 'no output')}" for prev in previous_results
        )
        parts.append("")

    return instructions, "\n".join(parts)


def build_reevaluate_prompt(
    goal: str,
    plan_markdown: str,
    latest_result: str,
) -> tuple[str, str]:
    """Build the re-evaluate reasoning call. Returns (instructions, user_message)."""
    instructions = (
        "Review the implementation plan in light of the latest completed work. "
        "Should remaining subtasks be changed, added, removed, or reordered? "
        'If no changes needed, respond with: {"no_changes": true}\n'
        "Otherwise respond with a JSON array of updated remaining subtasks: "
        '[{"description": "..."}]'
    )

    parts = [
        f"## Goal\n\n{goal}\n",
        f"## Current Plan\n\n{plan_markdown}\n",
        f"## Latest Completed Result\n\n{latest_result}\n",
    ]

    return instructions, "\n".join(parts)
