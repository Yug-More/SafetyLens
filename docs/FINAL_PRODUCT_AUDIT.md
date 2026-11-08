# Final product audit

Continuation baseline: `9c9315c28a43ead8ffebbafb68681def9fe0577a`, clean existing enhancement branch. Historical claims are rechecked, not treated as acceptance evidence.

## Confirmed blockers before this continuation

- README regression: two original inline screenshots and their captions, problem/solution narrative, staged-demo instructions and exact award wording disappeared from the main README. Original assets remain tracked; historical README alone is insufficient preservation in the primary presentation.
- Detection: conservative video-presence recall was 2/6. Frame-level diagnostic rerun is retained outside Git pending aggregate analysis; tracking loss and failed confirmation are separate observed failure classes. A synthetic transport/browser fixture does not verify an actual model-generated event.
- PPE: weights exist outside Git and ONNX inference loads; no labeled evaluation has yet established useful performance. Conflicting model-card/embedded licensing blocks commercial deployment. No deployment license is inferred from a manifest string.
- Camera worker: policies expose confidence and recording controls, but a live hardware fleet has never been validated. Browser preview is a latest-image interface, not streaming video with overlays. Missing models fail at runtime.
- Deployment: privileged Docker info still reports daemon unavailable at `/Users/amolair/.docker/run/docker.sock`. Only 2.5 GiB disk is free; image builds and additional runtimes may exceed it. Docker runtime must not be represented as passed.
- Setup: defaults depend on working directory; environment templates require first-use copying, administrator bootstrap and consistent localhost hostnames. Tests use isolated configured environments, which cannot alone prove the documented first-use path.

## Verification priorities

Restore primary README, reproduce individual misses with observations and inspect actual frames, freeze a justified candidate before acquiring untouched clips, run a labeled PPE benchmark with explicit training-overlap uncertainty, run actual recorded-media worker through authenticated application workflow, validate documented migrations/bootstrap/startup, expand browser coverage and preserve logs. Missing hardware/daemon/independent relation labels remain explicit acceptance blockers.

## Scope and evidence

Existing routes, services, migrations, detector engines, deployment and automated fixtures were inspected before edits. Historical implementation/report detail remains in PLATFORM_AUDIT.md and RELEASE_VERIFICATION.md; this document records newly established blockers rather than duplicating those inventories. Final gate outcomes belong in FINAL_RELEASE_REPORT.md.

## Additional reproduced integration defects

- Finite replay EOF was treated as camera failure: reconnect reopened the same file, generated fresh event UUIDs and could repeatedly report one recorded incident. EOF now consumes a replay once.
- Short clips could end before the requested post-event interval. Their active capture was discarded rather than delivered. Available frames now finalize with an explicit truncated-window limitation; shutdown also preserves partial evidence.
- A short replay could finish before the two-second transport tick. Final synchronous delivery is attempted; failures retain their durable queue entry.
- Worker replay sampling advanced from each rounded selected frame, unlike the evaluator's fixed sample clock, yielding fewer samples than configured. Replay now advances the fixed clock by its period.
- Docker Desktop was installed but stopped. Starting the application enabled daemon 28.5.1. The first build then failed because `docker-credential-desktop` was absent from shell PATH; a command-local Resources/bin PATH fixes discovery without editing personal Docker configuration.
