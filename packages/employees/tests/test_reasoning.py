"""Tests for CEO reasoning — JSON extraction and prompt builders."""

from __future__ import annotations

import pytest
from autogenesis_employees.reasoning import (
    build_assign_prompt,
    build_decompose_prompt,
    build_reevaluate_prompt,
    extract_json,
)


class TestExtractJson:
    def test_fenced_json_block(self):
        text = 'Here is the result:\n```json\n[{"description": "task 1"}]\n```\nDone.'
        result = extract_json(text)
        assert result == [{"description": "task 1"}]

    def test_raw_json_array(self):
        text = 'The tasks are: [{"description": "task 1"}, {"description": "task 2"}]'
        result = extract_json(text)
        assert len(result) == 2

    def test_raw_json_object(self):
        text = 'Result: {"employee_id": "backend-engineer", "reasoning": "best fit"}'
        result = extract_json(text)
        assert result["employee_id"] == "backend-engineer"

    def test_no_json_raises(self):
        with pytest.raises(ValueError, match="No JSON"):
            extract_json("This has no JSON in it at all.")

    def test_no_changes_object(self):
        text = '```json\n{"no_changes": true}\n```'
        result = extract_json(text)
        assert result["no_changes"] is True

    def test_multiline_fenced(self):
        text = (
            "```json\n"
            "[\n"
            '  {"description": "a", "rationale": "b"},\n'
            '  {"description": "c", "rationale": "d"}\n'
            "]\n"
            "```"
        )
        result = extract_json(text)
        assert len(result) == 2


class TestBuildDecomposePrompt:
    def test_returns_instructions_and_message(self):
        roster = [
            {"id": "be", "title": "Backend Engineer", "persona": "Writes APIs", "tools": ["shell"]},
        ]
        instructions, message = build_decompose_prompt(
            goal="Build user auth",
            roster_summary=roster,
            changelog_entries=["## 2026-03-19 — cto\n**Task:** setup"],
        )
        assert "CEO" in instructions
        assert "Build user auth" in message
        assert "Backend Engineer" in message
        assert "JSON" in instructions

    def test_empty_changelog(self):
        _instructions, message = build_decompose_prompt(
            goal="Build feature",
            roster_summary=[],
            changelog_entries=[],
        )
        assert "Build feature" in message


class TestBuildAssignPrompt:
    def test_returns_instructions_and_message(self):
        roster = [
            {
                "id": "be",
                "title": "Backend Engineer",
                "persona": "APIs",
                "tools": ["shell"],
                "training_directives": [],
            },
        ]
        instructions, message = build_assign_prompt(
            subtask="Build REST endpoint",
            goal_context="Building user auth",
            roster_details=roster,
            previous_results=[],
        )
        assert "best employee" in instructions.lower()
        assert "Build REST endpoint" in message
        assert "Building user auth" in message

    def test_with_previous_results(self):
        _instructions, message = build_assign_prompt(
            subtask="Write tests",
            goal_context="Building user auth",
            roster_details=[],
            previous_results=[{"subtask": "Build API", "result": "Done"}],
        )
        assert "Build API" in message


class TestBuildReevaluatePrompt:
    def test_returns_instructions_and_message(self):
        instructions, message = build_reevaluate_prompt(
            goal="Build user auth",
            plan_markdown="## Subtasks\n- [x] Build API\n- [ ] Write tests",
            latest_result="API complete",
        )
        assert "Review" in instructions or "review" in instructions
        assert "Build user auth" in message
        assert "API complete" in message
