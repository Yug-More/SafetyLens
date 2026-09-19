from __future__ import annotations

from .metrics import derive_pose_metrics
from .models import DetectorConfig, DetectorResult, DetectorState, PoseObservation
from .state_machine import FallStateMachine


class DetectorEngine:
    """Coordinates per-track metric history and temporal classification."""

    def __init__(self, config: DetectorConfig | None = None) -> None:
        self.machine = FallStateMachine(config)
        self._previous: dict[str, PoseObservation] = {}

    def process(self, observation: PoseObservation) -> DetectorResult:
        previous = self._previous.get(observation.track_id)
        metrics = derive_pose_metrics(observation, previous)
        old_state, state, event, reasons = self.machine.process(observation, metrics)
        if state == DetectorState.LOW_VISIBILITY:
            self._previous.pop(observation.track_id, None)
        else:
            self._previous[observation.track_id] = observation
        return DetectorResult(
            track_id=observation.track_id,
            previous_state=old_state,
            state=state,
            metrics=metrics,
            event=event,
            reasons=reasons,
        )

    def mark_missing(self, track_id: str) -> DetectorResult:
        old_state, state = self.machine.mark_missing(track_id)
        self._previous.pop(track_id, None)
        return DetectorResult(
            track_id=track_id,
            previous_state=old_state,
            state=state,
            metrics=None,
            reasons=("track_missing",),
        )
