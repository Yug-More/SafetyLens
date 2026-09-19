# SafetyLens temporal detector

This package owns the lightweight, continuous part of SafetyLens. It consumes timestamped pose landmarks, derives explainable motion/posture metrics, emits at most one `possible_person_down` event per fall episode, and retains a bounded pre/post-event evidence window. It does not diagnose injury, produce response instructions, or write to the main application database.

MediaPipe supplies the live and prerecorded pose observations. The metric engine and state machine can also consume recorded landmarks independently of that runtime, allowing future pose providers to reuse the event contract.

## State flow

```text
no_person -> monitoring -> suspected -> confirming -> incident -> cooldown
                  ^             |                         |
                  +-------------+-------------------------+
```

Low-quality poses enter `low_visibility`; a sustained absence enters `no_person`. Tracking resumes from fresh observations. A cooldown requires an upright recovery before rearming, preventing repeated alerts while a person remains on the floor. Confirmation has two paths: a rapid drop followed by persistent down posture, or persistent down posture followed by sustained low motion. Down posture uses torso angle and a guarded wide-body-box signal for curled poses. The optional overhead profile also uses relative shoulder displacement for views where lying lengthwise can still appear vertical in image coordinates.

## Run tests

From the repository root in PowerShell:

```powershell
$env:PYTHONPATH = "detector/src"
python -m unittest discover -s detector/tests -v
```

The tests use only the Python standard library. They cover a clear fall, normal standing, a temporary bend, poor visibility, timestamp errors, multiple tracks, and duplicate suppression.

## Replay pose observations

The replay command accepts JSON Lines with normalized image coordinates (`x` and `y` from 0 to 1):

```json
{"timestamp_seconds": 0.0, "track_id": "person-1", "landmarks": {"left_shoulder": [0.45, 0.25, 0.99], "right_shoulder": [0.55, 0.25, 0.99], "left_hip": [0.46, 0.55, 0.99], "right_hip": [0.54, 0.55, 0.99]}}
```

```powershell
$env:PYTHONPATH = "detector/src"
python -m safetylens_detector.replay path\to\poses.jsonl
```

Each landmark is `[x, y, visibility]`. The replay prints state transitions and complete event JSON. Values produced here are heuristic signals, not calibrated probability.

## Analyze a prerecorded video

Install the optional local-video runtime into a Python 3.11 or 3.12 environment:

```powershell
python -m pip install -e "detector[video]"
```

Download the MediaPipe Pose Landmarker Lite task to the ignored `detector/models` directory:

```powershell
New-Item -ItemType Directory -Path detector/models -Force
curl.exe -L --output detector/models/pose_landmarker_lite.task "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
```

Run a clip through pose estimation and the temporal state machine:

```powershell
$env:PYTHONPATH = "detector/src"
python -m safetylens_detector.video path\to\clip.mov `
  --model detector/models/pose_landmarker_lite.task `
  --sample-fps 12
```

The JSON result includes pose coverage, state transitions, and any emitted `possible_person_down` events. The first implementation tracks one person per camera and processes frames locally. `12 FPS` is the default because the state machine uses elapsed timestamps rather than frame counts.

Brief pose-estimation dropouts are tolerated for 0.5 seconds by default. A longer absence transitions the track to `no_person`; this prevents a single missed frame during a fall from erasing the candidate while still handling someone walking out of view.

## Run live camera detection

Use a Windows webcam index or a phone-camera stream URL:

```powershell
$env:PYTHONPATH = "detector/src"
python -m safetylens_detector.live `
  --source 0 `
  --model detector/models/pose_landmarker_lite.task `
  --sample-fps 12 `
  --mirror
```

The preview displays green `NORMAL` and red `FALL DETECTED`. After an incident, recovery requires a continuous upright pose for 0.6 seconds and the 4-second duplicate-suppression interval to finish. The detector then rearms for another fall. Brief upright glitches and missing poses do not clear an incident. Press `Q` to stop.

The default live profile uses body posture, with frame aspect ratio accounted for. Use a fixed camera with one full person visible. For a fixed overhead view where the body points toward the camera, `--overhead-camera` enables an additional shoulder-displacement heuristic. This heuristic is sensitive to camera movement and changes in distance; it is disabled in the default live profile. Prerecorded analysis retains its overhead-compatible default.

Completed incidents save a 3-second pre-event plus 3-second post-event MP4 under the ignored `detector/events` directory. Event JSON is saved immediately; session JSONL records pose measurements, state transitions, and event IDs for diagnosis. Allow three seconds after an alert before stopping to finish the evidence clip. These local records do not automatically create a backend incident; upload the evidence clip through the application for that workflow. The source may also be an OpenCV-compatible HTTP/RTSP URL, for example `--source "http://PHONE_IP:PORT/video"`.

For a phone exposed to Windows as a webcam, try `--source 1`, then `2`, while keeping `--source 0` for the built-in camera. The pose model and state machine still run locally on the laptop; only camera frames cross from the phone.

## Future development

1. Tune thresholds against positive and negative demo clips.
2. Add stable multi-person tracking and validate across camera positions.
3. Add retention controls and long-running camera recovery.
4. Automate delivery of saved event JSON and clips to `POST /api/detector/events` with retries and duplicate protection.

See the [detector contract](../docs/team/DETECTOR_CONTRACT.md) for the integration boundary and the [backend guide](../backend/README.md) for the implemented ingestion API.
