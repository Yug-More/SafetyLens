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
    horizontal_last_seen: float | None = None
    overhead_since: float | None = None
    overhead_last_seen: float | None = None
    low_motion_since: float | None = None
    incident_at: float | None = None
    recovered_after_incident: bool = False
    rapid_drop_seen: bool = False
    armed: bool = True
    baseline_shoulder_y: float | None = None
    recovery_since: float | None = None


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
                track.recovery_since = None
                if track.armed:
                    track.baseline_shoulder_y = None
                track.state = DetectorState.MONITORING if track.armed else DetectorState.COOLDOWN
        track.last_timestamp = observation.timestamp_seconds

        if metrics.pose_quality < self.config.minimum_pose_quality or metrics.torso_angle_degrees_from_vertical is None:
            track.recovery_since = None
            track.state = DetectorState.LOW_VISIBILITY
            self._clear_candidate(track)
            return previous_state, track.state, None, ("insufficient_pose_quality",)

        timestamp = observation.timestamp_seconds
        if track.baseline_shoulder_y is None and metrics.shoulder_center_y is not None:
            track.baseline_shoulder_y = metrics.shoulder_center_y
        overhead_displacement = (
            self.config.enable_overhead_displacement
            and metrics.shoulder_center_y is not None
            and track.baseline_shoulder_y is not None
            and metrics.shoulder_center_y - track.baseline_shoulder_y
            >= self.config.overhead_shoulder_drop_ratio
        )
        wide_tilted_pose = (
            metrics.bbox_width_height_ratio is not None
            and metrics.bbox_width_height_ratio >= self.config.down_bbox_width_height_ratio
            and metrics.torso_angle_degrees_from_vertical
            >= self.config.minimum_tilt_for_bbox_down_degrees
        )
        horizontal_angle_with_body_box = (
            metrics.bbox_width_height_ratio is not None
            and metrics.bbox_width_height_ratio
            >= self.config.minimum_horizontal_bbox_ratio
            and metrics.torso_angle_degrees_from_vertical
            >= self.config.horizontal_angle_degrees
        )
        horizontal = horizontal_angle_with_body_box or wide_tilted_pose
        upright = (
            not overhead_displacement
            and
            metrics.bbox_width_height_ratio is not None
            and metrics.bbox_width_height_ratio <= self.config.maximum_recovery_bbox_ratio
            and metrics.torso_angle_degrees_from_vertical
            <= self.config.recovery_angle_degrees
        )
        rapid_drop = (
            metrics.downward_hip_velocity_body_lengths_per_second is not None
            and metrics.downward_hip_velocity_body_lengths_per_second >= self.config.rapid_drop_velocity
        )
        low_motion = (
            metrics.mean_landmark_motion_body_lengths_per_second is not None
            and metrics.mean_landmark_motion_body_lengths_per_second <= self.config.low_motion_threshold
        )
        overhead_settled = (
            overhead_displacement
            and metrics.mean_landmark_motion_body_lengths_per_second is not None
            and metrics.mean_landmark_motion_body_lengths_per_second
            <= self.config.overhead_settled_motion_threshold
        )
        candidate_down = horizontal or overhead_displacement

        if track.state in {DetectorState.NO_PERSON, DetectorState.LOW_VISIBILITY}:
            track.state = DetectorState.MONITORING if track.armed else DetectorState.COOLDOWN

        if track.state == DetectorState.MONITORING:
            if metrics.shoulder_center_y is not None and not rapid_drop:
                track.baseline_shoulder_y = min(
                    track.baseline_shoulder_y
                    if track.baseline_shoulder_y is not None
                    else metrics.shoulder_center_y,
                    metrics.shoulder_center_y,
                )
            if rapid_drop or candidate_down:
                track.state = DetectorState.SUSPECTED
                track.suspected_at = timestamp
                track.rapid_drop_seen = rapid_drop
                track.horizontal_since = timestamp if horizontal else None
                track.horizontal_last_seen = timestamp if horizontal else None
                track.overhead_since = timestamp if overhead_settled else None
                track.overhead_last_seen = timestamp if overhead_settled else None
                track.low_motion_since = timestamp if horizontal and low_motion else None

        elif track.state == DetectorState.SUSPECTED:
            track.rapid_drop_seen = track.rapid_drop_seen or rapid_drop
            if candidate_down:
                track.state = DetectorState.CONFIRMING
                if horizontal:
                    track.horizontal_since = track.horizontal_since or timestamp
                    track.horizontal_last_seen = timestamp
                if overhead_settled:
                    track.overhead_since = track.overhead_since or timestamp
                    track.overhead_last_seen = timestamp
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
                    track.horizontal_last_seen = timestamp
                elif (
                    track.horizontal_last_seen is None
                    or timestamp - track.horizontal_last_seen
                    > self.config.down_posture_gap_tolerance_seconds
                ):
                    track.horizontal_since = None
                    track.horizontal_last_seen = None
                if overhead_settled:
                    track.overhead_since = track.overhead_since or timestamp
                    track.overhead_last_seen = timestamp
                elif (
                    track.overhead_last_seen is None
                    or timestamp - track.overhead_last_seen
                    > self.config.down_posture_gap_tolerance_seconds
                ):
                    track.overhead_since = None
                    track.overhead_last_seen = None
                if horizontal and low_motion:
                    track.low_motion_since = track.low_motion_since or timestamp
                else:
                    track.low_motion_since = None

                horizontal_duration = timestamp - track.horizontal_since if track.horizontal_since is not None else 0
                overhead_duration = (
                    timestamp - track.overhead_since
                    if track.overhead_since is not None
                    else 0
                )
                low_motion_duration = timestamp - track.low_motion_since if track.low_motion_since is not None else 0
                if (
                    (
                        horizontal_duration >= self.config.horizontal_hold_seconds
                        and (
                            track.rapid_drop_seen
                            or low_motion_duration >= self.config.low_motion_hold_seconds
                        )
                    )
                    or (
                        track.rapid_drop_seen
                        and overhead_duration >= self.config.overhead_hold_seconds
                    )
                ):
                    track.state = DetectorState.INCIDENT
                    track.incident_at = timestamp
                    track.armed = False
                    event = self._event(
                        observation,
                        metrics,
                        rapid_drop=track.rapid_drop_seen,
                        low_motion_confirmed=(
                            low_motion_duration >= self.config.low_motion_hold_seconds
                        ),
                        bbox_posture=wide_tilted_pose,
                        overhead_displacement=overhead_displacement,
                    )
                    return previous_state, track.state, event, event.trigger_signals

        elif track.state == DetectorState.INCIDENT:
            track.state = DetectorState.COOLDOWN

        elif track.state == DetectorState.COOLDOWN:
            if upright:
                if track.recovery_since is None:
                    track.recovery_since = timestamp
                track.recovered_after_incident = (
                    timestamp - track.recovery_since >= self.config.recovery_hold_seconds
                )
            else:
                track.recovery_since = None
                track.recovered_after_incident = False
            cooldown_elapsed = (
                track.incident_at is not None
                and timestamp - track.incident_at >= self.config.cooldown_seconds
            )
            if cooldown_elapsed and track.recovered_after_incident:
                track.state = DetectorState.MONITORING
                track.armed = True
                self._reset_temporal_state(track)
                track.baseline_shoulder_y = metrics.shoulder_center_y

        reasons = tuple(
            reason
            for condition, reason in (
                (rapid_drop, "rapid_drop"),
                (horizontal, "horizontal_posture"),
                (wide_tilted_pose, "wide_tilted_body_box"),
                (overhead_displacement, "downward_body_displacement"),
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
        track.recovery_since = None
        track.recovered_after_incident = False
        if track.armed:
            track.baseline_shoulder_y = None
        self._clear_candidate(track)
        return previous, track.state

    def _event(
        self,
        observation: PoseObservation,
        metrics: PoseMetrics,
        rapid_drop: bool,
        low_motion_confirmed: bool,
        bbox_posture: bool,
        overhead_displacement: bool,
    ) -> DetectionEvent:
        signals = ["down_posture_persistence"]
        if rapid_drop:
            signals.insert(0, "rapid_drop")
        if bbox_posture:
            signals.append("wide_tilted_body_box")
        if overhead_displacement:
            signals.append("downward_body_displacement")
        if low_motion_confirmed:
            signals.append("low_motion_persistence")
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
            limitations=(
                "single_person_pose_heuristic",
                "not_a_medical_diagnosis",
                "requires_human_verification",
            ),
        )

    @staticmethod
    def _clear_candidate(track: TrackState) -> None:
        track.suspected_at = None
        track.horizontal_since = None
        track.horizontal_last_seen = None
        track.overhead_since = None
        track.overhead_last_seen = None
        track.low_motion_since = None
        track.rapid_drop_seen = False

    @classmethod
    def _reset_temporal_state(cls, track: TrackState) -> None:
        cls._clear_candidate(track)
        track.incident_at = None
        track.recovered_after_incident = False
        track.recovery_since = None
