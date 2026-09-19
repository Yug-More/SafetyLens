# SafetyLens team build plan

Prepared September 19, 2026. Read this with ABHINAV_HANDOFF.md and DETECTOR_CONTRACT.md.

## Current baseline and direction

Verified shared baseline: `origin/main` at `598eaf8`, which merges Stage 3 (`build/video-pipeline`, `8e6d796`). It includes the dashboard, FastAPI/SQLite backend, video upload, processing jobs, OpenCV metadata/frame sampling, playback, and frame timeline. All new teammate work branches start from this integrated main baseline, or a newer main commit after fetching.

Target: Track 1 AI Assistants. Keep Yug's broad product and stage sequence for now. Demonstrate one worker-fall journey first; additional event categories can remain supported by the analysis schema without Sean building detectors for every category. Camera monitoring supplies evidence to an assistant that explains, retrieves policy, and coordinates approved simulated actions.

## Ownership

| Owner | Deliverables | Owned paths | Branch |
|---|---|---|---|
| Yug | Existing video upload; Stage 4 multimodal analysis; Stage 5 SOP retrieval/cited plans; Stage 6 approval/execution/audit/PDF report; Stage 7 integration/deployment | `backend/**`, existing frontend pages/components/API clients, root configuration/README | Keep sequential `build/multimodal-analysis`, `build/policy-response`, `build/action-execution`, `build/hackathon-release` |
| Sean | Continuous input, pose metrics, temporal fall detection, evidence buffer, detector tests/measurements | New `detector/**`; `docs/team/DETECTOR_CONTRACT.md` | `codex/sean-fall-detector` |
| Abhinav (Abinav) | Small demo-help page, manual rehearsal/QA checklist, three-minute demo script | New `frontend/src/app/demo-help/**`, `frontend/src/components/demo-help/**`, `docs/demo/**`, `docs/DEMO_SCRIPT.md` | `codex/abhinav-demo-support` |
| Sean, this handoff | Coordination documents only | `docs/team/**` | `codex/team-handoff` |

Ownership means one writer per shared file, even on separate branches. Branches isolate edits; they do not automatically prevent conflicts. Changes to someone else's area need a short coordination message and a named integration owner. Yug owns shared API/schema changes and merges application contributions. Sean owns detector changes. Abhinav reports defects outside his paths with reproduction steps instead of expanding his patch.

## How Yug's uploaded stages are distributed

The uploaded remaining-stages PDF is planning input. Its sequence remains Yug's workstream: finish and verify 4, then 5, then 6, then 7. Keep its real/demo provider separation, schema validation, exact citations, explicit approvals, simulated-action labels, tests, and commit/push checkpoints.

Two explicit adjustments avoid duplication:

1. Sean develops the detector independently while Yug develops Stages 4-6. Sean does not replace Stage 3 upload/frame sampling or implement a competing analysis API.
2. Abhinav owns Stage 7's `docs/DEMO_SCRIPT.md`, a new isolated demo-help route, and manual QA evidence. Yug should skip regenerating those owned files and integrate them at Stage 7. Yug retains global styling, navigation, release cleanup, automated evaluation, reset/fallback behavior, judge Q&A, and deployment.

Stage 4's instruction to return no incident when evidence is insufficient should retain a distinction between inconclusive evidence and a clear negative. Low visibility must not become a confident safe result.

## Git protocol for all three

Start from origin/main, then remain on your own branch. Before each session: `git status --short --branch`, `git fetch origin`, and (if upstream exists) `git pull --ff-only`. Stop on unexpected local changes or divergence; inspect, preserve, and resolve with the owner. Never force-push, reset away work, or overwrite unrelated changes. Check the branch name before every commit and push.

Pulling your own branch does not bring in Yug's new stages. Yug publishes the approved integration base and commit when it changes. At a clean checkpoint, merge that named remote branch into your work branch with coordination; do not repeatedly rebase published branches. Yug merges completed teammate branches into his current stage/integration branch, verifies, and then creates the next stage branch. Merge into main only through the team's reviewed integration process.

Starting commands (after ensuring a clean tree):

```sh
git fetch origin
git switch -c codex/sean-fall-detector origin/main
# Abhinav instead uses codex/abhinav-demo-support; see his handoff.
```

If your branch already exists locally, switch to it instead of recreating it. If only the remote branch exists, use `git switch --track origin/BRANCH`. Before committing, inspect `git diff` and `git diff --cached`; stage only owned paths. Commit and push every completed, verified unit. Share branch, commit, changed paths, tests, and blockers. Do not push every keystroke or claim untested work passes.

The planning branch is based on main at 598eaf8 and contains only new handoff docs. Teammates can read these on GitHub without changing branches. Yug can merge its documentation PR into main, then synchronize his stage branch with main at a clean checkpoint. Branch creation/push for Sean and Abhinav belongs to their actual work sessions. The planning branch is not Sean's implementation branch.

## Sequencing and integration gates

1. All: confirm baseline, ownership and branch; run baseline checks and record pre-existing failures.
2. Sean: implement pure metrics/state machine and synthetic temporal tests; then one prerecorded stream processed in real time; then webcam; buffer and event export. Benchmark on the actual machine. RTSP and phone transport follow only after this works.
3. Yug: continue Stage 4 with existing uploaded videos immediately; no dependency on live detection. Then Stages 5 and 6 per his PDF.
4. Abhinav: implement demo-help and manual checklist independently; write script with clearly marked future steps. Rehearse the current Stage 3 app. After each integrated stage, update actual observations.
5. Sean + Yug: connect a detector-produced clip to the existing upload endpoint; use its returned asset code for Stage 4 analysis. Yug owns backend mapping. Agree and verify duplicate-event handling before automatic handoff.
6. Yug: integrate Abhinav's route (add one navigation link himself), detector adapter, and remaining Stage 7 release work. All rehearse the same integrated commit.

## Completion and scope decisions

Keep the broad screens and roadmap. If time or reliability becomes a problem, defer in order: phone/WebRTC and background push, multiple cameras, extra detector classes, optional embeddings, and secondary analytics polish. Protect the one complete upload/detection -> analysis -> cited plan -> approval -> simulated action -> report path. Use explicit demo providers when selected; never silently label mocked analysis as real.

Live detection is a prototype until measured. Earlier discussion of FPS and RTX 2050 capacity was feasibility estimation, not a benchmark. Do not present pose confidence or heuristic scores as calibrated fall probability. Use recorded consented/licensed clips for falls; do not ask anyone to perform a dangerous fall.

## Validation ownership

Yug: complete backend suite, frontend typecheck/lint/build, analysis/retrieval/approval integration and failures. Sean: state-transition tests, negatives, tracking loss, duplicate suppression, FPS/latency and false alarms on named clips. Abhinav: frontend checks plus visible desktop/mobile route review and a reproducible manual checklist. Each reports what was actually run. Planning documents alone do not establish that application checks pass.
