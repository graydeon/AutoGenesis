"""Tests for project slug derivation."""

from __future__ import annotations

from autogenesis_employees.project import get_project_slug, slugify


class TestSlugify:
    def test_basic(self):
        assert slugify("AutoGenesis") == "autogenesis"

    def test_spaces_and_special(self):
        assert slugify("My Cool Project!") == "my-cool-project"

    def test_strips_hyphens(self):
        assert slugify("--test--") == "test"


class TestGetProjectSlug:
    def test_uses_cwd_basename(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        slug = get_project_slug()
        assert slug == slugify(tmp_path.name)

    def test_uses_config_project_name(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        config_dir = tmp_path / ".autogenesis"
        config_dir.mkdir()
        (config_dir / "config.yaml").write_text("project_name: MyProject")
        slug = get_project_slug()
        assert slug == "myproject"
