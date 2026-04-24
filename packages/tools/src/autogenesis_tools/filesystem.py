"""File read/write/edit/glob/grep tools."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from autogenesis_security.sandbox import SecurityPolicyError, WorkspacePolicy

from autogenesis_tools.base import Tool

_MAX_READ_BYTES = 1_000_000  # 1MB


class _WorkspaceToolMixin:
    def __init__(self, *, workspace_root: str | Path | None = None) -> None:
        self._workspace = WorkspacePolicy(Path(workspace_root) if workspace_root else Path.cwd())

    def _resolve_path(self, path: str | Path) -> Path:
        return self._workspace.resolve_path(path)


class FileReadTool(_WorkspaceToolMixin, Tool):
    """Read file contents with optional line range."""

    @property
    def name(self) -> str:
        return "file_read"

    @property
    def description(self) -> str:
        return "Read a file's contents, optionally specifying a line range."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
                "start_line": {"type": "integer", "description": "Start line (1-based)"},
                "end_line": {"type": "integer", "description": "End line (inclusive)"},
            },
            "required": ["path"],
        }

    @property
    def token_cost_estimate(self) -> int:
        return 150

    async def execute(self, arguments: dict[str, Any]) -> str:
        """Read file contents."""
        try:
            path = self._resolve_path(arguments["path"])
        except SecurityPolicyError as exc:
            return f"Error: {exc}"
        if not path.exists():
            return f"Error: File not found: {path}"

        size = path.stat().st_size
        if size > _MAX_READ_BYTES:
            return f"Error: File too large ({size} bytes, max {_MAX_READ_BYTES})"

        content = path.read_text(errors="replace")
        lines = content.splitlines(keepends=True)

        start = arguments.get("start_line", 1)
        end = arguments.get("end_line", len(lines))
        selected = lines[max(0, start - 1) : end]

        numbered = [f"{i + start:>6}\t{line}" for i, line in enumerate(selected)]
        return "".join(numbered)


class FileWriteTool(_WorkspaceToolMixin, Tool):
    """Write content to a file, creating directories as needed."""

    @property
    def name(self) -> str:
        return "file_write"

    @property
    def description(self) -> str:
        return "Write content to a file. Creates parent directories if needed."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        }

    @property
    def token_cost_estimate(self) -> int:
        return 150

    async def execute(self, arguments: dict[str, Any]) -> str:
        """Write content to file."""
        try:
            path = self._resolve_path(arguments["path"])
        except SecurityPolicyError as exc:
            return f"Error: {exc}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(arguments["content"])
        return f"Wrote {len(arguments['content'])} chars to {path}"


class FileEditTool(_WorkspaceToolMixin, Tool):
    """Edit a file by replacing an exact string match."""

    @property
    def name(self) -> str:
        return "file_edit"

    @property
    def description(self) -> str:
        return "Replace an exact string in a file. The old_str must appear exactly once."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to edit"},
                "old_str": {"type": "string", "description": "Exact string to find"},
                "new_str": {"type": "string", "description": "Replacement string"},
            },
            "required": ["path", "old_str", "new_str"],
        }

    @property
    def token_cost_estimate(self) -> int:
        return 200

    async def execute(self, arguments: dict[str, Any]) -> str:
        """Replace exact string in file."""
        try:
            path = self._resolve_path(arguments["path"])
        except SecurityPolicyError as exc:
            return f"Error: {exc}"
        if not path.exists():
            return f"Error: File not found: {path}"

        content = path.read_text()
        old_str = arguments["old_str"]
        count = content.count(old_str)

        if count == 0:
            return "Error: old_str not found in file"
        if count > 1:
            return f"Error: old_str found {count} times (must be unique)"

        new_content = content.replace(old_str, arguments["new_str"], 1)
        path.write_text(new_content)
        return "Edit applied successfully"


class GlobTool(_WorkspaceToolMixin, Tool):
    """Find files matching a glob pattern."""

    @property
    def name(self) -> str:
        return "glob"

    @property
    def description(self) -> str:
        return "Find files matching a glob pattern."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern (e.g. **/*.py)"},
                "path": {"type": "string", "description": "Base directory (default: .)"},
            },
            "required": ["pattern"],
        }

    @property
    def token_cost_estimate(self) -> int:
        return 100

    async def execute(self, arguments: dict[str, Any]) -> str:
        """Find files matching glob pattern."""
        try:
            base = self._resolve_path(arguments.get("path", "."))
        except SecurityPolicyError as exc:
            return f"Error: {exc}"
        pattern = arguments["pattern"]
        matches = sorted(str(p) for p in base.glob(pattern) if p.is_file())
        if not matches:
            return "No files found"
        return "\n".join(matches)


class GrepTool(_WorkspaceToolMixin, Tool):
    """Search file contents with regex."""

    @property
    def name(self) -> str:
        return "grep"

    @property
    def description(self) -> str:
        return "Search files for a regex pattern."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern"},
                "path": {"type": "string", "description": "File or directory to search"},
                "context": {"type": "integer", "description": "Context lines (default 0)"},
            },
            "required": ["pattern", "path"],
        }

    @property
    def token_cost_estimate(self) -> int:
        return 100

    async def execute(self, arguments: dict[str, Any]) -> str:
        """Search for regex pattern in files."""
        try:
            path = self._resolve_path(arguments["path"])
        except SecurityPolicyError as exc:
            return f"Error: {exc}"
        pattern = re.compile(arguments["pattern"])
        ctx = arguments.get("context", 0)
        results: list[str] = []

        files = [path] if path.is_file() else sorted(path.rglob("*"))

        for file_path in files:
            if not file_path.is_file():
                continue
            try:
                lines = file_path.read_text(errors="replace").splitlines()
            except (PermissionError, OSError):
                continue

            for i, line in enumerate(lines):
                if pattern.search(line):
                    start = max(0, i - ctx)
                    end = min(len(lines), i + ctx + 1)
                    for j in range(start, end):
                        prefix = ">" if j == i else " "
                        results.append(f"{file_path}:{j + 1}:{prefix}{lines[j]}")

        if not results:
            return "No matches found"
        return "\n".join(results[:200])


class ListDirTool(_WorkspaceToolMixin, Tool):
    """List directory contents."""

    @property
    def name(self) -> str:
        return "list_dir"

    @property
    def description(self) -> str:
        return "List files and directories in a path."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path (default: .)"},
                "depth": {"type": "integer", "description": "Max depth (default 1)"},
            },
        }

    @property
    def token_cost_estimate(self) -> int:
        return 80

    async def execute(self, arguments: dict[str, Any]) -> str:
        """List directory contents."""
        try:
            path = self._resolve_path(arguments.get("path", "."))
        except SecurityPolicyError as exc:
            return f"Error: {exc}"
        depth = arguments.get("depth", 1)
        if not path.is_dir():
            return f"Error: Not a directory: {path}"

        entries: list[str] = []
        hidden_names = {".", "..", "node_modules", "__pycache__", ".git"}

        def _walk(p: Path, current_depth: int) -> None:
            if current_depth > depth:
                return
            try:
                for child in sorted(p.iterdir()):
                    if child.name in hidden_names:
                        continue
                    prefix = "  " * current_depth
                    suffix = "/" if child.is_dir() else ""
                    entries.append(f"{prefix}{child.name}{suffix}")
                    if child.is_dir():
                        _walk(child, current_depth + 1)
            except PermissionError:
                pass

        _walk(path, 0)
        return "\n".join(entries) if entries else "Empty directory"
