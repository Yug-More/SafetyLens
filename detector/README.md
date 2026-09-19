# SafetyLens temporal detector

This package owns the lightweight, continuous part of SafetyLens. It consumes timestamped pose landmarks, derives explainable motion/posture metrics, emits at most one `possible_person_down` event per fall episode, and retains a bounded pre/post-event evidence window. It does not diagnose injury, produce response instructions, or write to the main application database.

The initial milestone is deliberately independent of a pose runtime. MediaPipe, MoveNet, or a small YOLO pose model can implement the `PoseProvider` protocol after a local benchmark. The temporal logic and event contract remain the same.

## State flow

```text
no_person -> monitoring -> suspected -> confirming -> incident -> cooldown
                  ^             |                         |
                  +-------------+-------------------------+
```

Low-quality or missing landmarks enter `low_visibility`. Tracking resumes only from fresh observations. A cooldown requires an upright recovery before rearming, preventing repeated alerts while a person remains on the floor. Confirmation has two paths: a rapid drop followed by persistent down posture, or persistent down posture followed by sustained low motion. Down posture uses torso angle plus a guarded wide-body-box signal so curled floor poses are not missed.

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

## Next milestone

1. Tune thresholds against positive and negative demo clips.
2. Connect webcam input to the same observation pipeline.
3. Encode buffered frames into an incident clip.
4. Export the event clip through Yug's existing `POST /api/videos/upload` workflow.

See `docs/team/DETECTOR_CONTRACT.md` for the integration boundary.
