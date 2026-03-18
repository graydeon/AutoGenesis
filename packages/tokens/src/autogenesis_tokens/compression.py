"""Context compression via output truncation and observation masking."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from autogenesis_core.models import Message


_MAX_TOOL_OUTPUT_CHARS = 500


class ContextCompressor:
    """Compress conversation context by truncating old tool outputs.

    Strategy: Keep recent messages intact, truncate older tool outputs
    to reduce token count while preserving conversation structure.
    """

    def __init__(
        self,
        max_tool_output_chars: int = _MAX_TOOL_OUTPUT_CHARS,
        recent_turns_to_keep: int = 6,
    ) -> None:
        self._max_chars = max_tool_output_chars
        self._recent = recent_turns_to_keep

    def compress(self, messages: list[Message]) -> list[Message]:
        """Compress messages by truncating old tool outputs.

        Returns a new list with truncated copies (originals not modified).
        """
        if len(messages) <= self._recent:
            return list(messages)

        cutoff = len(messages) - self._recent
        result: list[Message] = []

        for i, msg in enumerate(messages):
            if i < cutoff and msg.role == "tool" and isinstance(msg.content, str):
                content = msg.content
                if len(content) > self._max_chars:
                    original_len = len(content)
                    truncated = content[: self._max_chars]
                    masked = f"{truncated}\n[output truncated — {original_len} chars]"
                    result.append(msg.model_copy(update={"content": masked}))
                    continue
            result.append(msg)

        return result

    def estimate_reduction(self, messages: list[Message]) -> float:
        """Estimate the compression ratio (0.0 = no reduction, 1.0 = all removed)."""
        if not messages:
            return 0.0
        original_chars = sum(len(m.content) if isinstance(m.content, str) else 0 for m in messages)
        if original_chars == 0:
            return 0.0
        compressed = self.compress(messages)
        compressed_chars = sum(
            len(m.content) if isinstance(m.content, str) else 0 for m in compressed
        )
        return 1.0 - (compressed_chars / original_chars)
