"""Tests for tool and MCP server allowlisting."""

from __future__ import annotations

from autogenesis_security.allowlist import MCPAllowlist, ToolAllowlist


class TestToolAllowlist:
    def test_default_allows_all(self):
        al = ToolAllowlist()
        assert al.is_allowed("bash") is True
        assert al.is_allowed("anything") is True

    def test_explicit_allowlist(self):
        al = ToolAllowlist(allowed=["bash", "file_read"])
        assert al.is_allowed("bash") is True
        assert al.is_allowed("dangerous_tool") is False

    def test_add_to_allowlist(self):
        al = ToolAllowlist(allowed=["bash"])
        al.add("file_read")
        assert al.is_allowed("file_read") is True


class TestMCPAllowlist:
    def test_default_allows_all(self):
        al = MCPAllowlist()
        assert al.is_allowed("any_server") is True

    def test_explicit_allowlist(self):
        al = MCPAllowlist(allowed=["trusted_server"])
        assert al.is_allowed("trusted_server") is True
        assert al.is_allowed("untrusted") is False

    def test_hash_pinning(self):
        al = MCPAllowlist()
        config = {"command": "node", "args": ["server.js"]}
        al.pin("server1", config)
        assert al.verify_hash("server1", config) is True

        # Modified config should fail
        modified = {"command": "node", "args": ["evil.js"]}
        assert al.verify_hash("server1", modified) is False

    def test_no_pin_always_passes(self):
        al = MCPAllowlist()
        assert al.verify_hash("unpinned", {"any": "config"}) is True
