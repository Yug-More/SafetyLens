# Yug: stage sequence and team integration

Continue the remaining stages in your PDF, in order. The team is keeping the broad scope for now. Main now contains Stage 3 at 598eaf8, so new work can branch from origin/main. Preserve your existing Stage 4 branch if already underway; do not recreate it or lose local changes.

## Paste into your AI

> Read docs/team/TEAM_PLAN.md, ABHINAV_HANDOFF.md and DETECTOR_CONTRACT.md, or the provided text if the planning branch has not merged. Inspect status, fetch and synchronize the current branch before working. Main includes Stage 3 at 598eaf8. If starting Stage 4 fresh, create build/multimodal-analysis from origin/main. If Stage 4 already exists, resume it and preserve all changes. Keep the remaining PDF's sequential Stage 4 -> 5 -> 6 -> 7 workflow and validation gates. Subsequent stage branches can retain the PDF's names and start from the verified previous stage. Do not implement multiple stages simultaneously.
>
> Yug owns the main backend, database, uploaded-video pipeline, AI providers, retrieval/planning, approvals, execution, reports, shared frontend, and deployment. Sean owns detector/** and live fall metrics/state machine/evidence buffering. Abhinav owns frontend/src/app/demo-help/**, frontend/src/components/demo-help/**, docs/demo/** and docs/DEMO_SCRIPT.md. Reserve those files: Stage 7 should integrate his work rather than regenerate it. Keep broad product scope, with one fall journey as the first completed demo. Sean's detector must not block analysis of existing uploaded videos.
>
> Integrate detector clips using the existing video upload/processing contract, followed by Stage 4 analysis. Implement the shared API adapter and event-id deduplication on Yug's side after agreeing the version 1 event contract. Do not treat a pose-quality score as fall probability. Keep inconclusive evidence distinct from a confirmed no-incident result. Keep real/demo provider behavior explicit, citations verified, and simulated actions clearly labeled as specified by the stage PDF.
>
> Commit and push verified stage milestones to your branch. Coordinate integration of teammate branches at clean checkpoints; this team integration task is an explicit adjustment to the PDF's no-merge instruction for individual stage execution. Stage implementation alone does not authorize arbitrary merges. Review the exact contribution, integrate into the current continuing stage branch, run combined checks, and carry it into the next stage branch. Main changes go through reviewed PRs. Do not force-push or rewrite teammates' history. Report branch/commit, tests, current integrated baseline, and any integration changes needed from Sean or Abhinav.

## Immediate coordination message

Tell Sean and Abhinav your active branch and current commit, and whether Stage 4 has begun. Abhinav can start his independent page now. Sean can start detector work now. Tell both when a new integrated main/stage baseline is ready. A pull on their feature branch will not automatically incorporate your changes.

## Integration checklist

- Review incoming file paths against ownership before merging.
- Merge docs/team planning first so everyone can read the handoffs from the repo.
- Add Abhinav's demo-help navigation entry yourself; he uses the direct URL meanwhile.
- Give Sean actual camera database IDs and the analysis endpoint shape once Stage 4 exists.
- Run backend pytest and frontend typecheck/lint/build on the combined tree, then rehearse the path being demonstrated.
- Keep future steps marked pending until implemented; don't turn the demo checklist into claimed test results.
