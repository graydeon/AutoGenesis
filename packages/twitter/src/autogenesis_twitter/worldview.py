"""Worldview state management — CRUD with bounding and pruning.

The worldview is a structured summary of the agent's accumulated
observations and opinions. It is bounded to prevent unbounded growth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autogenesis_twitter.models import WorldviewState

if TYPE_CHECKING:
    from pathlib import Path

_MAX_TOPICS = 20
_MAX_PEOPLE = 50
_MAX_OPINIONS = 30


class WorldviewManager:
    """Manages the agent's worldview state on disk."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> WorldviewState:
        """Load worldview from disk, creating default if missing."""
        if not self._path.exists():
            state = WorldviewState()
            self.save(state)
            return state
        return WorldviewState.model_validate_json(self._path.read_text())

    def save(self, state: WorldviewState) -> None:
        """Save worldview to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(state.model_dump_json(indent=2))

    def prune(self, state: WorldviewState) -> WorldviewState:
        """Enforce bounding rules on worldview state."""
        if len(state.topics_of_interest) > _MAX_TOPICS:
            state.topics_of_interest = state.topics_of_interest[-_MAX_TOPICS:]
        if len(state.people_i_engage_with) > _MAX_PEOPLE:
            state.people_i_engage_with = state.people_i_engage_with[-_MAX_PEOPLE:]
        if len(state.opinions_formed) > _MAX_OPINIONS:
            state.opinions_formed = state.opinions_formed[-_MAX_OPINIONS:]
        return state

    def add_topic(self, state: WorldviewState, topic: str) -> None:
        """Add a topic if not already present."""
        if topic not in state.topics_of_interest:
            state.topics_of_interest.append(topic)

    def add_person(self, state: WorldviewState, handle: str) -> None:
        """Add a person if not already present."""
        if handle not in state.people_i_engage_with:
            state.people_i_engage_with.append(handle)
