from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .models import DetectionEvent, DetectorConfig, DetectorState, PoseMetrics, PoseObservation


@dataclass
class TrackState:
    state: DetectorState = DetectorState.NO_PERSON
    last_timestamp: float | None = None
    suspected_at: float | None = None
    horizontal_since: float | None = None
    low_motion_since: float | None = None
    incident_at: float | None = None
    recovered_after_incident: bool = False
    rapid_drop_seen: bool = False
    armed: bool = True


class FallStateMachine:
    def __init__(self, config: DetectorConfig | None = None) -> None:
        self.config = config or DetectorConfig()
        self._tracks: dict[str, TrackState] = {}

    def get_state(self, track_id: str) -> DetectorState:
        return self._tracks.get(track_id, TrackState()).state

    def process(
        self,
        observation: PoseObservation,
        metrics: PoseMetrics,
    ) -> tuple[DetectorState, DetectorState, DetectionEvent | None, tuple[str, ...]]:
        track = self._tracks.setdefault(observation.track_id, TrackState())
        previous_state = track.state

        if track.last_timestamp is not None:
            if observation.timestamp_seconds <= track.last_timestamp:
                raise ValueError("Observation timestamps must strictly increase per track.")
            if observation.timestamp_seconds - track.last_timestamp > self.config.maximum_observation_gap_seconds:
                self._clear_candidate(track)
                track.state = DetectorState.MONITORING if track.armed else DetectorState.COOLDOWN
        track.last_timestamp = observation.timestamp_seconds

        if metrics.pose_quality < self.config.minimum_pose_quality or metrics.torso_angle_degrees_from_vertical is None:
            track.state = DetectorState.LOW_VISIBILITY
            self._clear_candidate(track)
            return previous_state, track.state, None, ("insufficient_pose_quality",)

        timestamp = observation.timestamp_seconds
        horizontal = metrics.torso_angle_degrees_from_vertical >= self.config.horizontal_angle_degrees
        upright = metrics.torso_angle_degrees_from_vertical <= self.config.recovery_angle_degrees
        rapid_drop = (
            metrics.downward_hip_velocity_body_lengths_per_second is not None
            and metrics.downward_hip_velocity_body_lengths_per_second >= self.config.rapid_drop_velocity
        )
        low_motion = (
            metrics.mean_landmark_motion_body_lengths_per_second is not None
            and metrics.mean_landmark_motion_body_lengths_per_second <= self.config.low_motion_threshold
        )

        if track.state in {DetectorState.NO_PERSON, DetectorState.LOW_VISIBILITY}:
            track.state = DetectorState.MONITORING if track.armed else DetectorState.COOLDOWN

        if track.state == DetectorState.MONITORING:
            if rapid_drop or horizontal:
                track.state = DetectorState.SUSPECTED
                track.suspected_at = timestamp
                track.rapid_drop_seen = rapid_drop
                track.horizontal_since = timestamp if horizontal else None
                track.low_motion_since = timestamp if horizontal and low_motion else None

        elif track.state == DetectorState.SUSPECTED:
            track.rapid_drop_seen = track.rapid_drop_seen or rapid_drop
            if horizontal:
                track.state = DetectorState.CONFIRMING
                track.horizontal_since = track.horizontal_since or timestamp
                track.low_motion_since = timestamp if low_motion else None
            elif track.suspected_at is not None and timestamp - track.suspected_at > self.config.suspicion_timeout_seconds:
                track.state = DetectorState.MONITORING
                self._clear_candidate(track)

        elif track.state == DetectorState.CONFIRMING:
            if upright:
                track.state = DetectorState.MONITORING
                self._clear_candidate(track)
            else:
                if horizontal:
                    track.horizontal_since = track.horizontal_since or timestamp
                else:
                    track.horizontal_since = None
                if horizontal and low_motion:
                    track.low_motion_since = track.low_motion_since or timestamp
                else:
                    track.low_motion_since = None

                horizontal_duration = timestamp - track.horizontal_since if track.horizontal_since is not None else 0
                low_motion_duration = timestamp - track.low_motion_since if track.low_motion_since is not None else 0
                if (
                    horizontal_duration >= self.config.horizontal_hold_seconds
                    and low_motion_duration >= self.config.low_motion_hold_seconds
                ):
                    track.state = DetectorState.INCIDENT
                    track.incident_at = timestamp
                    track.armed = False
                    event = self._event(observation, metrics, track.rapid_drop_seen)
                    return previous_state, track.state, event, event.trigger_signals

        elif track.state == DetectorState.INCIDENT:
            track.state = DetectorState.COOLDOWN

        elif track.state == DetectorState.COOLDOWN:
            if upright:
                track.recovered_after_incident = True
            cooldown_elapsed = (
                track.incident_at is not None
                and timestamp - track.incident_at >= self.config.cooldown_seconds
            )
            if cooldown_elapsed and track.recovered_after_incident:
                track.state = DetectorState.MONITORING
                track.armed = True
                self._reset_temporal_state(track)

        reasons = tuple(
            reason
            for condition, reason in (
                (rapid_drop, "rapid_drop"),
                (horizontal, "horizontal_posture"),
                (low_motion, "low_motion"),
            )
            if condition
        )
        return previous_state, track.state, None, reasons

    def mark_missing(self, track_id: str) -> tuple[DetectorState, DetectorState]:
        track = self._tracks.setdefault(track_id, TrackState())
        previous = track.state
        track.state = DetectorState.NO_PERSON
        track.last_timestamp = None
        self._clear_candidate(track)
        return previous, track.state

    def _event(
        self,
        observation: PoseObservation,
        metrics: PoseMetrics,
        rapid_drop: bool,
    ) -> DetectionEvent:
        signals = ["horizontal_persistence", "low_motion_persistence"]
        if rapid_drop:
            signals.insert(0, "rapid_drop")
        return DetectionEvent(
            schema_version="1.0",
            event_id=str(uuid4()),
            event_type="possible_person_down",
            source_id=observation.source_id,
            track_id=observation.track_id,
            occurred_at_seconds=observation.timestamp_seconds,
            source_timestamp_seconds=observation.source_timestamp_seconds,
            state=DetectorState.INCIDENT,
            trigger_signals=tuple(signals),
            pose_quality=metrics.pose_quality,
            metrics=metrics,
        )

    @staticmethod
    def _clear_candidate(track: TrackState) -> None:
        track.suspected_at = None
        track.horizontal_since = None
        track.low_motion_since = None
        track.rapid_drop_seen = False

    @classmethod
    def _reset_temporal_state(cls, track: TrackState) -> None:
        cls._clear_candidate(track)
        track.incident_at = None
        track.recovered_after_incident = False
