"""Conservative interpretation over the preserved legacy temporal algorithm.

A person down without a rapid descent is never labeled as an observed fall.
This is experimental, not a calibrated fall probability or a learned classifier.
"""

from dataclasses import dataclass, replace
from enum import Enum
from .engine import DetectorEngine
from .models import DetectorConfig, DetectorState


class SafetyState(str, Enum):
    NORMAL = "NORMAL"
    POSSIBLE_FALL = "POSSIBLE_FALL"
    FALL_DETECTED = "FALL_DETECTED"
    PERSON_DOWN = "PERSON_DOWN"
    RECOVERED = "RECOVERED"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class EnhancedResult:
    raw: object
    safety_state: SafetyState

    @property
    def event(self):
        return self.raw.event


class EnhancedDetectorEngine:
    def __init__(self, config=None):
        self.config = config or DetectorConfig(enable_overhead_displacement=False)
        self.engine = DetectorEngine(self.config)
        self.active = {}

    def process(self, observation):
        previous = self.engine._previous.get(observation.track_id)
        if (
            previous
            and observation.timestamp_seconds - previous.timestamp_seconds
            > self.config.maximum_observation_gap_seconds
        ):
            self.engine._previous.pop(observation.track_id, None)
        result = self.engine.process(observation)
        had_incident = self.active.get(observation.track_id, False)
        if result.event:
            falling = "rapid_drop" in result.event.trigger_signals
            event = replace(
                result.event,
                event_type="possible_person_down"
                if falling
                else "prolonged_person_down",
                limitations=(
                    *result.event.limitations,
                    "uncalibrated_temporal_rules",
                    "falling_motion_observed"
                    if falling
                    else "falling_motion_not_observed",
                ),
            )
            result = replace(result, event=event)
            self.active[observation.track_id] = True
            state = SafetyState.FALL_DETECTED if falling else SafetyState.PERSON_DOWN
        elif result.state in {DetectorState.NO_PERSON, DetectorState.LOW_VISIBILITY}:
            state = SafetyState.INCONCLUSIVE
        elif result.state == DetectorState.COOLDOWN:
            state = SafetyState.PERSON_DOWN
        elif had_incident and result.state == DetectorState.MONITORING:
            state = SafetyState.RECOVERED
            self.active[observation.track_id] = False
        elif result.state in {DetectorState.SUSPECTED, DetectorState.CONFIRMING}:
            state = SafetyState.POSSIBLE_FALL
        else:
            state = SafetyState.NORMAL
        return EnhancedResult(result, state)

    def mark_missing(self, track_id):
        return EnhancedResult(
            self.engine.mark_missing(track_id), SafetyState.INCONCLUSIVE
        )

    def forget_track(self, track_id):
        """Discard expired/ambiguous identities; never bridge motion across people."""
        self.engine._previous.pop(track_id, None)
        self.engine.machine._tracks.pop(track_id, None)
        self.active.pop(track_id, None)
