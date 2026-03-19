"""Tests for HR operations — hire, fire, train."""

from __future__ import annotations

import pytest
import yaml
from autogenesis_employees.hr import fire, hire, train


class TestHire:
    def test_hire_from_template(self, tmp_path):
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        (template_dir / "backend-engineer.yaml").write_text(
            yaml.dump(
                {
                    "id": "backend-engineer",
                    "title": "Backend Engineer",
                    "persona": "You are a backend engineer.",
                    "tools": ["bash"],
                    "status": "active",
                    "hired_at": "2026-03-19",
                }
            )
        )
        target_dir = tmp_path / "employees"
        target_dir.mkdir()

        hire(
            "Data Engineer",
            based_on="backend-engineer",
            template_dir=template_dir,
            target_dir=target_dir,
        )

        new_file = target_dir / "data-engineer.yaml"
        assert new_file.exists()
        data = yaml.safe_load(new_file.read_text())
        assert data["id"] == "data-engineer"
        assert data["title"] == "Data Engineer"

    def test_hire_duplicate_raises(self, tmp_path):
        target_dir = tmp_path / "employees"
        target_dir.mkdir()
        (target_dir / "existing.yaml").write_text(yaml.dump({"id": "existing"}))

        with pytest.raises(FileExistsError):
            hire("Existing", based_on=None, template_dir=tmp_path, target_dir=target_dir)


class TestFire:
    def test_archives_employee(self, tmp_path):
        (tmp_path / "be.yaml").write_text(
            yaml.dump(
                {
                    "id": "be",
                    "title": "BE",
                    "persona": "p",
                    "status": "active",
                }
            )
        )
        fire("be", config_dir=tmp_path)
        data = yaml.safe_load((tmp_path / "be.yaml").read_text())
        assert data["status"] == "archived"


class TestTrain:
    def test_appends_directive(self, tmp_path):
        (tmp_path / "be.yaml").write_text(
            yaml.dump(
                {
                    "id": "be",
                    "title": "BE",
                    "persona": "p",
                    "training_directives": [],
                    "status": "active",
                }
            )
        )
        train("be", "Always use type hints", config_dir=tmp_path)
        data = yaml.safe_load((tmp_path / "be.yaml").read_text())
        assert "Always use type hints" in data["training_directives"]
