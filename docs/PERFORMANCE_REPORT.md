# Measured performance

## Conditions and sources

Verified host: Apple M2 Pro,16GiB RAM, macOS14.5 arm64. Detector Python3.12.12, MediaPipe0.10.21 CPU delegate; model and dataset hashes are in `evaluation/hardening`. CPU resource values come from macOS `/usr/bin/time -l`; user+system seconds divided by wall time are reported on a **one-core basis**, so percentages may exceed100. RSS values are process resident memory, not total platform memory or GPU memory. Runtime profiling was not an isolated production load experiment.

## Offline inference comparison

Thirty new recording/camera clips,12 target input samples/s:

- Preserved original comparison:76.23 analyzed FPS;19.52s wall;24.33 process CPU seconds;124.64% one-core basis;451,575,808 bytes peak RSS.
- Calibrated Lite:75.96 FPS;19.61s wall;24.07 CPU seconds;122.74%;409,354,240 bytes RSS.
- Full:57.44 FPS;25.29s wall;29.90 CPU seconds;118.23%;395,460,608 bytes RSS.
- Lite four-pose:52.08 FPS;27.82s wall;32.85 CPU seconds;118.08%;375,291,904 bytes RSS.

These rates count sampled inference frames, not full source-frame throughput or live-camera capacity. Memory differences are single-process maxima from separate runs and should not be interpreted as a reproducible model-memory ranking. Full/multi-pose did not establish a reliability improvement sufficient to replace the default. Quality and camera-specific results are in DETECTION_VALIDATION.md.

## Four concurrent recorded cameras

`scripts/verify_camera_load.py` registered four cameras with the same recorded fall clip and ran the actual worker/inference/delivery threads.252 sampled frames completed in2.536s including process startup:99.36 aggregate offline sampled FPS. Each camera processed63 frames and delivered one acknowledged event. Process CPU4.99s user+2.24s system over2.52s tool wall (286.90% one-core basis); peak RSS668,106,752 bytes. Raw per-camera counters: `camera-load.json`; profiling: `performance.json`.

This is a short repeated-recording load check, not four independent scenes, sustained RTSP operation or a promise of supported camera count on arbitrary hardware. It does demonstrate that the four-thread path ran actual inference and persisted four distinct camera events. Dropped frames are null because no accurate counter exists; they are not silently reported as zero.

A local prerecorded MJPEG camera was interrupted at4s and resumed at8s. Observed health: online2.400s, offline4.615s, online12.666s. Recovery includes exponential reconnect backoff. This measures a controlled network simulation, not a hardware or internet outage SLA.

## API, workflow and storage

Final PostgreSQL17 Compose verification,30 sequential warm authenticated camera-inventory requests: minimum5.476ms, mean6.719ms, maximum19.296ms. No p95/SLO or concurrent query capacity is inferred. Two simultaneous authenticated incident updates produced200/409 as intended. Backend/database restart and private backup tests are separate reliability evidence, not a query benchmark.

The actual offline worker's final recorded path took2.355s from process/model start through recording/delivery acknowledgement. This is not physical fall-to-UI latency. Publisher-matched default event delays averaged1.258 video-seconds on four detections, with six missed events retained. Operator notification existed and browser SSE/refetch paths passed; separately synchronized live notification latency was not measured.

A quiescent media snapshot contained88 files in a4,300,800-byte tar archive; every file hash matched after isolated restoration. This is a snapshot size, not a per-camera/day storage estimate. No representative industrial bitrate, retention-cost or database-query saturation benchmark has been conducted. GPU utilization and total-platform CPU/RAM remain unmeasured. PPE per-image timings are preserved in its raw output and do not imply useful detection quality.

## Reproduce

Use the dataset acquisition/evaluation commands in DETECTION_VALIDATION.md, prefixing model commands with `/usr/bin/time -l` on macOS. On Linux, resource units differ. Full-stack scripts are in DEPLOYMENT_VERIFICATION.md; load/reconnect requires isolated private QA credentials and writes only task-specific cameras/volumes. Do not reuse its repeated scene to claim independent accuracy or hardware fleet readiness.
