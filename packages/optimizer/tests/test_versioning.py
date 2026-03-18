"""Tests for prompt version control."""

from __future__ import annotations

from autogenesis_optimizer.versioning import PromptVersionManager


class TestPromptVersionManager:
    def test_create_version_with_checksum(self, tmp_path):
        vm = PromptVersionManager(tmp_path / "prompts")
        pv = vm.create_version("core", "You are helpful.", "1.0.0")

        assert pv.version == "1.0.0"
        assert pv.checksum.startswith("sha256:")
        assert pv.content == "You are helpful."

    def test_semver_chain(self, tmp_path):
        vm = PromptVersionManager(tmp_path / "prompts")
        vm.create_version("core", "V1", "1.0.0")
        vm.create_version("core", "V2", "1.1.0", parent_version="1.0.0")

        versions = vm.list_versions("core")
        assert "1.0.0" in versions
        assert "1.1.0" in versions

    def test_active_version_tracking(self, tmp_path):
        vm = PromptVersionManager(tmp_path / "prompts")
        vm.create_version("core", "V1", "1.0.0")

        assert vm.get_active_version("core") == "1.0.0"

        vm.create_version("core", "V2", "1.1.0")
        vm.set_active_version("core", "1.1.0")
        assert vm.get_active_version("core") == "1.1.0"

    def test_manifest_yaml_persistence(self, tmp_path):
        prompts_dir = tmp_path / "prompts"
        vm1 = PromptVersionManager(prompts_dir)
        vm1.create_version("core", "V1", "1.0.0")

        vm2 = PromptVersionManager(prompts_dir)
        assert vm2.get_active_version("core") == "1.0.0"

    def test_rollback(self, tmp_path):
        vm = PromptVersionManager(tmp_path / "prompts")
        vm.create_version("core", "V1", "1.0.0")
        vm.create_version("core", "V2", "1.1.0", parent_version="1.0.0")
        vm.set_active_version("core", "1.1.0")

        result = vm.rollback("core")
        assert result == "1.0.0"
        assert vm.get_active_version("core") == "1.0.0"

    def test_checksum_integrity(self, tmp_path):
        vm = PromptVersionManager(tmp_path / "prompts")
        vm.create_version("core", "Hello", "1.0.0")

        checksum = vm.get_checksum("core", "1.0.0")
        assert checksum is not None
        assert checksum.startswith("sha256:")
