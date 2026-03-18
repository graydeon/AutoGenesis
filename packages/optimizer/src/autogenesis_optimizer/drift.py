"""Drift detection for prompt quality metrics."""

from __future__ import annotations

from dataclasses import dataclass

from autogenesis_core.events import Event, EventType, get_event_bus


@dataclass
class DriftResult:
    """Result of a drift check."""

    drifted: bool
    metric_diffs: dict[str, float]
    alerts: list[str]


class DriftDetector:
    """Detect drift in prompt quality metrics."""

    def __init__(self, threshold: float = 0.1) -> None:
        self._threshold = threshold

    def check(
        self,
        baseline_scores: dict[str, float],
        current_scores: dict[str, float],
    ) -> DriftResult:
        """Compare current scores to baseline. Detect degradation."""
        diffs: dict[str, float] = {}
        alerts: list[str] = []

        for metric, baseline_val in baseline_scores.items():
            current_val = current_scores.get(metric, 0.0)
            diff = current_val - baseline_val
            diffs[metric] = diff

            if diff < -self._threshold:
                alerts.append(
                    f"Drift detected: {metric} dropped by {abs(diff):.3f}"
                    f" (baseline={baseline_val:.3f}, current={current_val:.3f})"
                )

        drifted = len(alerts) > 0

        if drifted:
            bus = get_event_bus()
            bus.emit(
                Event(
                    event_type=EventType.PROMPT_VERSION_CHANGE,
                    data={"drift": True, "alerts": alerts},
                )
            )

        return DriftResult(drifted=drifted, metric_diffs=diffs, alerts=alerts)
