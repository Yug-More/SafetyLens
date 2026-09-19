# Sean's detector work and integration contract

Status: proposed version 1 contract; detector and adapter are not implemented by this planning commit. Yug owns application integration. Keep runtime artifacts ignored with detector-local ignore rules. No shared requirements or API schema edits in the first detector milestones.

## Deliverables

Build in `detector/` on `codex/sean-fall-detector` from origin/main (598eaf8 or newer). Pure metrics and temporal state tests first; video replay and webcam through the same pipeline second; local evidence buffering and export third. Use a small pretrained pose model selected after a local smoke benchmark. Keep dependencies isolated. Phone streaming/RTSP are extensions after one source is stable.

State progression: no_person -> monitoring -> suspected -> confirming -> incident -> cooldown. Recovery before confirmation returns to monitoring. Low keypoint quality or tracking loss produces unknown/low_visibility; never treats disappearance as recovery or adds unobserved time to immobility. Camera reconnect and source changes reset per-track history. After an incident, rearm only with a defined recovery/new-track rule and cooldown to prevent repeated incidents for one person lying down.

Use elapsed monotonic capture time, not frame counts alone. Track people separately. Combine visible posture transition, normalized vertical motion, horizontal/low posture persistence and low motion. Floor-relative height is only meaningful with explicit scene calibration; otherwise report image-relative metrics. Distinguish a detected transition from a person already lying down when monitoring starts.

## Proposed event fields

```json
{
  "schema_version": "1.0",
  "event_id": "unique-event-id",
  "event_type": "possible_person_down",
  "source_id": "demo-camera-04",
  "camera_id": null,
  "track_id": "track-1",
  "occurred_at": "2026-09-19T17:05:46Z",
  "source_timestamp_seconds": 12.4,
  "clip_event_offset_seconds": 8.0,
  "state": "incident",
  "trigger_signals": ["rapid_drop", "horizontal_persistence"],
  "pose_quality": 0.91,
  "heuristic_score": null,
  "metrics": {
    "torso_angle_degrees_from_vertical": 76,
    "downward_hip_velocity_body_lengths_per_second": 0.31,
    "horizontal_duration_seconds": 2.1,
    "low_motion_duration_seconds": 3.0
  },
  "evidence": {
    "clip_relative_path": "events/unique-event-id/clip.mp4",
    "pre_event_seconds": 8,
    "post_event_seconds": 6,
    "frame_offsets_seconds": [0, 4, 8, 10, 13]
  },
  "limitations": []
}
```

Numbers above illustrate shape and units, not tuned thresholds or observed accuracy. Null means unavailable, not zero. Pose quality measures landmark reliability; any heuristic score is not calibrated probability. Do not populate the app's AI `confidence` from pose quality. source_id is a detector label; camera_id, when provided, must be the real database ID returned by the camera API, not the display string cam-04. Event and media timestamps must state their coordinate system.

## Integration with existing Stage 3 and Yug's Stage 4

1. Detector exports an incident clip locally and one event JSON with stable event_id. Keep raw media local until the configured application handoff.
2. An adapter uploads the clip via existing `POST /api/videos/upload` multipart fields: file, location, optional real camera_id. Read the returned asset_code and job_code from the data envelope.
3. Poll `GET /api/processing-jobs/{job_code}` until job status is completed or failed, with bounded timeout; video status separately becomes ready. Yug's pipeline owns storage/frame extraction and existing frame IDs.
4. Once Stage 4 exists, use `POST /api/videos/{asset_code}/analyze`. It is not present in Stage 3. Model evidence references must resolve to actual VideoFrame records, not detector paths or guessed IDs.
5. Yug maps event_id to asset_code and prevents duplicate active ingestion/analysis. Retries must reuse that mapping; the current upload endpoint is not assumed idempotent. Agree where this mapping lives before automating retries.
6. Initial integration uses existing sampling. If it misses the short event, Yug adjusts sampling around clip_event_offset_seconds in one coordinated patch; Sean supplies offsets, not a replacement storage service.

The detector may expose a local metrics viewer/CLI in its own folder. Yug owns embedding metrics/video in the main Monitor component. Do not store absolute workstation paths in public API responses. An unacknowledged event or upload failure must be visible and retryable without pretending analysis completed.

## Evidence and measurement

Track FPS, inference latency, dropped frames, trigger latency from labeled event onset, duplicate events and false alerts per minute. Evaluate fall clips and ordinary standing, walking, sitting, bending, lying down intentionally, camera occlusion, and re-entry. Report clip counts and hardware; a tiny fixture set cannot establish production accuracy. Unit tests cover transitions at differing frame rates, missing landmarks, recovery, multiple tracks, timestamp discontinuity, buffer bounds and cooldown.

Milestone acceptance: replay triggers from measured frames rather than a hard-coded timestamp; ordinary negative clips do not trigger under stated conditions; one event per incident; selected evidence includes the transition; webcam uses the same metrics/state machine; all failures and model/runtime choices are documented. Keep known-video replay available for demonstration. Do not delay an initial visible suspected-event indication while waiting for the post-event buffer or cloud verification. Critical response logic remains Yug's human-reviewed workflow.
