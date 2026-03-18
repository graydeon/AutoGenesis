"""Tests for drift detection."""

from __future__ import annotations

from autogenesis_core.events import EventType, get_event_bus
from autogenesis_optimizer.drift import DriftDetector


class TestDriftDetector:
    def test_detect_score_drop(self):
        detector = DriftDetector(threshold=0.1)
        baseline = {"quality": 0.9, "safety": 0.95}
        current = {"quality": 0.7, "safety": 0.95}

        result = detector.check(baseline, current)
        assert result.drifted is True
        assert len(result.alerts) == 1
        assert "quality" in result.alerts[0]

    def test_no_drift_when_stable(self):
        detector = DriftDetector(threshold=0.1)
        baseline = {"quality": 0.9, "safety": 0.95}
        current = {"quality": 0.88, "safety": 0.94}

        result = detector.check(baseline, current)
        assert result.drifted is False
        assert len(result.alerts) == 0

    def test_alert_emission(self):
        bus = get_event_bus()
        events = []
        bus.subscribe(EventType.PROMPT_VERSION_CHANGE, events.append)

        detector = DriftDetector(threshold=0.1)
        detector.check(
            {"quality": 0.9},
            {"quality": 0.5},
        )

        assert len(events) >= 1

    def test_threshold_configuration(self):
        strict = DriftDetector(threshold=0.01)
        lenient = DriftDetector(threshold=0.5)

        baseline = {"quality": 0.9}
        current = {"quality": 0.85}

        assert strict.check(baseline, current).drifted is True
        assert lenient.check(baseline, current).drifted is False
