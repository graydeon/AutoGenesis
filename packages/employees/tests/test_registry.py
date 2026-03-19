"""Tests for employee registry — YAML config loading and merging."""

from __future__ import annotations

import yaml
from autogenesis_employees.registry import EmployeeRegistry


class TestEmployeeRegistry:
    def test_load_from_directory(self, tmp_path):
        (tmp_path / "cto.yaml").write_text(
            yaml.dump(
                {
                    "id": "cto",
                    "title": "CTO",
                    "persona": "You are the CTO.",
                    "tools": ["bash"],
                    "status": "active",
                    "hired_at": "2026-03-19",
                }
            )
        )
        reg = EmployeeRegistry(global_dir=tmp_path)
        employees = reg.list_active()
        assert len(employees) == 1
        assert employees[0].id == "cto"

    def test_skips_archived(self, tmp_path):
        (tmp_path / "old.yaml").write_text(
            yaml.dump(
                {
                    "id": "old",
                    "title": "Old",
                    "persona": "p",
                    "status": "archived",
                }
            )
        )
        reg = EmployeeRegistry(global_dir=tmp_path)
        assert len(reg.list_active()) == 0

    def test_project_override_merges(self, tmp_path):
        global_dir = tmp_path / "global"
        global_dir.mkdir()
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        (global_dir / "be.yaml").write_text(
            yaml.dump(
                {
                    "id": "be",
                    "title": "Backend Engineer",
                    "persona": "Base persona.",
                    "tools": ["bash"],
                    "status": "active",
                }
            )
        )
        (project_dir / "be.yaml").write_text(
            yaml.dump(
                {
                    "training_directives": ["Use async/await always"],
                }
            )
        )

        reg = EmployeeRegistry(global_dir=global_dir, project_dir=project_dir)
        be = reg.get("be")
        assert be is not None
        assert be.persona == "Base persona."
        assert "Use async/await always" in be.training_directives

    def test_get_nonexistent(self, tmp_path):
        reg = EmployeeRegistry(global_dir=tmp_path)
        assert reg.get("nope") is None

    def test_list_all_includes_archived(self, tmp_path):
        (tmp_path / "a.yaml").write_text(
            yaml.dump(
                {
                    "id": "a",
                    "title": "A",
                    "persona": "p",
                    "status": "active",
                }
            )
        )
        (tmp_path / "b.yaml").write_text(
            yaml.dump(
                {
                    "id": "b",
                    "title": "B",
                    "persona": "p",
                    "status": "archived",
                }
            )
        )
        reg = EmployeeRegistry(global_dir=tmp_path)
        assert len(reg.list_all()) == 2
        assert len(reg.list_active()) == 1
