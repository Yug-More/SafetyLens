# Fall-only submission handoff

This scope supersedes broader plans for submission. Preserve team work but demonstrate one
problem: a possible fall needs evidence review and a traceable response. No smoke/PPE,
injury diagnosis, emergency dispatch, or commercial-readiness claims.

## Ownership

- Sean: pose/video detection, state machine, detector JSON contract, integration regression checks.
- Yug: analysis/retrieval/planning, approval, simulated execution, audit, reports.
- Abhinav: demo guide, wording, rehearsal checklist, screenshots and manual UI QA. Freedom to
  improve clarity; avoid detector thresholds/backend contracts before submission.

All work is integrated on main. Start new scoped edits on separate branches from refreshed
main. Coordinate overlapping files. Preserve uncommitted changes; never force-reset teammates.

```powershell
git status
git fetch origin
git switch -c codex/abinav-demo-polish origin/main
# Make and test changes, then:
git add <specific-files>
git commit -m "Polish fall demo guide"
git push -u origin codex/abinav-demo-polish
```

Use distinct branch names for Sean/Yug. Open a PR; one integrator merges into main.
Without GitHub sign-in, local branching/commits still work. Resolve sign-in or share a patch;
never share tokens or copy files over another person's checkout.

## Reliable demo path

Use a consented prerecorded fall; Camo/live video is not a dependency. From `detector/`,
with the video extra and model installed per its README:

```powershell
$env:PYTHONPATH = 'src'
..\backend\.venv\Scripts\python.exe -m safetylens_detector.video "C:\path\fall.mov" --model models/pose_landmarker_lite.task --output output/fall-result.json
```

In Live Monitor → Detector handoff choose JSON and the **same original video**. The importer
accepts one event or a video result containing exactly one event; zero-event negatives must
not create incidents. For a cropped live clip use its matching event with clip-relative offset.
Wait for processing/analysis, refresh the list, and open evidence. In Response Center choose
the matching analysis in the policy workspace, retrieve fall SOP, inspect citations, generate
plan, approve selected actions, execute simulation, inspect audit, generate/download PDF.
The seeded demo incident is reused intentionally, not production multi-incident routing.
Ordinary upload is a fallback workflow demo, **not a detector run**.

## Start and verify

Backend (`backend/`, Python 3.12 recommended):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.seed.run
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8100
```

Backend `.env`: `FRONTEND_ORIGINS=http://localhost:3000,http://127.0.0.1:3000`.
Frontend `.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8100`.
From `frontend/`, install with its lockfile/package manager and run `pnpm dev`.
Open http://localhost:3000; API docs http://localhost:8100/docs.
Port 8100 avoids Sean's Windows excluded port-8000 range.

Default Demo AI and Demo Planner are scripted, not visual verification. Real providers need
separate configuration and validation. Do not switch just before judging. Keep environment
files, videos, keys and runtime databases out of Git.

```powershell
# backend/
.\.venv\Scripts\python.exe -m pytest -q
# detector/
$env:PYTHONPATH = 'src'
..\backend\.venv\Scripts\python.exe -m unittest discover -s tests
# frontend/
pnpm exec eslint .
pnpm exec tsc --noEmit
pnpm build
```

Preserve existing databases: create_all adds tables, not column migrations. Use a separate
seeded demo database if schema drift occurs; do not delete originals. Demo Reset deletes
runtime demo records and should only be used intentionally.

## Validation boundary

Prior tuning checks at 8/12/15 FPS: three staged falls each produced one candidate; walking
out of frame and sitting produced zero. Same person/setup and used for tuning: **not independent
accuracy validation**. Pose quality is landmark reliability, not fall probability. New camera
angles, occlusion, multiple people and intentional lying down remain risks. Not a medical or
emergency safety system.
