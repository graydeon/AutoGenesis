"""Interview system — conversational persona review.

Loads the agent's worldview state and enables a Q&A session
where the user can probe the agent's formed opinions and views.
Transcripts are saved for review.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from autogenesis_twitter.models import WorldviewState


def get_interview_dir() -> Path:
    """Get the directory for storing interview transcripts."""
    xdg = os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))
    return Path(xdg) / "autogenesis" / "twitter_interviews"


def format_worldview_for_prompt(state: WorldviewState) -> str:
    """Format worldview state as context for the interview."""
    parts = ["## Your Current Worldview\n"]

    if state.topics_of_interest:
        parts.append(f"**Topics you follow:** {', '.join(state.topics_of_interest)}")
    if state.people_i_engage_with:
        parts.append(f"**People you engage with:** {', '.join(state.people_i_engage_with[:10])}")
    if state.opinions_formed:
        parts.append("**Opinions you've formed:**")
        parts.extend(f"- {op.topic}: {op.stance}" for op in state.opinions_formed)
    if state.engagement_stats.style_notes:
        parts.append(f"**Style notes:** {state.engagement_stats.style_notes}")

    return "\n".join(parts)


def save_transcript(
    messages: list[dict[str, str]],
    directory: Path | None = None,
) -> Path:
    """Save interview transcript to disk."""
    directory = directory or get_interview_dir()
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d-%H%M%S")
    path = directory / f"{timestamp}.json"
    path.write_text(json.dumps(messages, indent=2))
    return path
