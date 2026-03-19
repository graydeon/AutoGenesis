"""Tests for worldview state management and bounding."""

from __future__ import annotations

from autogenesis_twitter.models import Opinion, WorldviewState
from autogenesis_twitter.worldview import WorldviewManager


class TestWorldviewManager:
    def test_load_creates_default(self, tmp_path):
        path = tmp_path / "worldview.json"
        mgr = WorldviewManager(path)
        state = mgr.load()
        assert state.topics_of_interest == []
        assert path.exists()

    def test_save_and_load(self, tmp_path):
        path = tmp_path / "worldview.json"
        mgr = WorldviewManager(path)
        state = WorldviewState(topics_of_interest=["AI safety"])
        mgr.save(state)
        loaded = mgr.load()
        assert "AI safety" in loaded.topics_of_interest

    def test_prune_topics_max_20(self, tmp_path):
        path = tmp_path / "worldview.json"
        mgr = WorldviewManager(path)
        state = WorldviewState(topics_of_interest=[f"topic_{i}" for i in range(25)])
        pruned = mgr.prune(state)
        assert len(pruned.topics_of_interest) <= 20

    def test_prune_people_max_50(self, tmp_path):
        path = tmp_path / "worldview.json"
        mgr = WorldviewManager(path)
        state = WorldviewState(people_i_engage_with=[f"@user_{i}" for i in range(60)])
        pruned = mgr.prune(state)
        assert len(pruned.people_i_engage_with) <= 50

    def test_prune_opinions_max_30(self, tmp_path):
        path = tmp_path / "worldview.json"
        mgr = WorldviewManager(path)
        opinions = [Opinion(topic=f"topic_{i}", stance="for", date="2026-01-01") for i in range(35)]
        state = WorldviewState(opinions_formed=opinions)
        pruned = mgr.prune(state)
        assert len(pruned.opinions_formed) <= 30

    def test_add_topic(self, tmp_path):
        path = tmp_path / "worldview.json"
        mgr = WorldviewManager(path)
        state = WorldviewState()
        mgr.add_topic(state, "AI safety")
        assert "AI safety" in state.topics_of_interest

    def test_add_topic_no_duplicates(self, tmp_path):
        path = tmp_path / "worldview.json"
        mgr = WorldviewManager(path)
        state = WorldviewState(topics_of_interest=["AI safety"])
        mgr.add_topic(state, "AI safety")
        assert state.topics_of_interest.count("AI safety") == 1
