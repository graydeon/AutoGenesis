"""Tests for filesystem tools."""

from __future__ import annotations

from autogenesis_core.models import ToolCall
from autogenesis_tools.filesystem import (
    FileEditTool,
    FileReadTool,
    FileWriteTool,
    GlobTool,
    GrepTool,
    ListDirTool,
)


class TestFileReadTool:
    async def test_read_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("line1\nline2\nline3\n")
        tool = FileReadTool()
        tc = ToolCall(name="file_read", arguments={"path": str(f)})
        result = await tool(tc)
        assert "line1" in result
        assert "line3" in result

    async def test_read_nonexistent(self):
        tool = FileReadTool()
        tc = ToolCall(name="file_read", arguments={"path": "/nonexistent/file.txt"})
        result = await tool(tc)
        assert "not found" in result.lower()

    async def test_read_line_range(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("a\nb\nc\nd\ne\n")
        tool = FileReadTool()
        tc = ToolCall(name="file_read", arguments={"path": str(f), "start_line": 2, "end_line": 4})
        result = await tool(tc)
        assert "b" in result
        assert "d" in result


class TestFileWriteTool:
    async def test_write_file(self, tmp_path):
        f = tmp_path / "output.txt"
        tool = FileWriteTool()
        tc = ToolCall(name="file_write", arguments={"path": str(f), "content": "hello world"})
        result = await tool(tc)
        assert "Wrote" in result
        assert f.read_text() == "hello world"

    async def test_auto_mkdir(self, tmp_path):
        f = tmp_path / "sub" / "dir" / "file.txt"
        tool = FileWriteTool()
        tc = ToolCall(name="file_write", arguments={"path": str(f), "content": "nested"})
        await tool(tc)
        assert f.read_text() == "nested"


class TestFileEditTool:
    async def test_edit_replace(self, tmp_path):
        f = tmp_path / "edit.txt"
        f.write_text("hello world")
        tool = FileEditTool()
        tc = ToolCall(
            name="file_edit",
            arguments={"path": str(f), "old_str": "world", "new_str": "earth"},
        )
        result = await tool(tc)
        assert "success" in result.lower()
        assert f.read_text() == "hello earth"

    async def test_edit_no_match(self, tmp_path):
        f = tmp_path / "edit.txt"
        f.write_text("hello world")
        tool = FileEditTool()
        tc = ToolCall(
            name="file_edit",
            arguments={"path": str(f), "old_str": "missing", "new_str": "x"},
        )
        result = await tool(tc)
        assert "not found" in result.lower()

    async def test_edit_multiple_matches(self, tmp_path):
        f = tmp_path / "edit.txt"
        f.write_text("aa bb aa")
        tool = FileEditTool()
        tc = ToolCall(
            name="file_edit",
            arguments={"path": str(f), "old_str": "aa", "new_str": "cc"},
        )
        result = await tool(tc)
        assert "2 times" in result


class TestGlobTool:
    async def test_glob_finds_files(self, tmp_path):
        (tmp_path / "a.py").write_text("# a")
        (tmp_path / "b.py").write_text("# b")
        (tmp_path / "c.txt").write_text("c")
        tool = GlobTool()
        tc = ToolCall(name="glob", arguments={"pattern": "*.py", "path": str(tmp_path)})
        result = await tool(tc)
        assert "a.py" in result
        assert "b.py" in result
        assert "c.txt" not in result


class TestGrepTool:
    async def test_grep_finds_pattern(self, tmp_path):
        f = tmp_path / "search.txt"
        f.write_text("foo bar\nbaz qux\nfoo baz\n")
        tool = GrepTool()
        tc = ToolCall(name="grep", arguments={"pattern": "foo", "path": str(f)})
        result = await tool(tc)
        assert "foo bar" in result
        assert "foo baz" in result


class TestListDirTool:
    async def test_list_dir(self, tmp_path):
        (tmp_path / "file.txt").write_text("x")
        (tmp_path / "subdir").mkdir()
        tool = ListDirTool()
        tc = ToolCall(name="list_dir", arguments={"path": str(tmp_path)})
        result = await tool(tc)
        assert "file.txt" in result
        assert "subdir/" in result
