# Abhinav: demo support handoff

Your scope is small but visible: help a judge or teammate understand and rehearse SafetyLens. You own a new demo-help page, a short demo script, and a checklist. Choose the page layout, icons, wording, and checklist presentation within the existing design. You do not need to build the AI or detector.

## 1. Create your branch manually

Git works locally even when an AI editor's GitHub connector does not. Open a normal terminal in your existing SafetyLens clone (the path is YOUR clone, not Sean's Windows path).

```sh
git status --short --branch
git remote -v
git fetch origin
git switch -c codex/abhinav-demo-support origin/main
git branch --show-current
```

Expected branch: `codex/abhinav-demo-support`. Main now includes Stage 3 at merge commit `598eaf8`. Fetch first so you use the current main baseline. If Yug explicitly gives a newer integration base, use that named branch instead.

If the branch already exists: `git switch codex/abhinav-demo-support`. If it exists only on GitHub: `git switch --track origin/codex/abhinav-demo-support`. Do not rerun branch creation blindly. If status shows existing edits, preserve/commit them on their intended branch first; ask your AI to inspect, not discard them.

If fetch/push says authentication failed or repository access denied, sign in manually using GitHub Desktop or `gh auth login` if GitHub CLI is installed, and ensure Yug has invited your account as a collaborator. Accept the invitation. Never paste tokens into code, chat, or the remote URL. An AI connector is optional; repository permission is still required for pushing.

If offline, and your locally fetched origin/main includes 598eaf8, local branch creation still works from that snapshot. Check with `git log -5 --oneline origin/main`. Otherwise get the current repository/baseline first. You may work and commit offline, but explicitly report that nothing has been pushed. Branches do not fix missing GitHub permissions.

## 2. Your tasks, in order

1. Run the existing app and see video upload/playback before editing.
2. Add `frontend/src/app/demo-help/page.tsx`; any new components go in `frontend/src/components/demo-help/`. Visit `/demo-help` directly; Yug will add navigation when integrating.
3. Show a short explanation, a readable demo sequence, and a rehearsal checklist. Link to existing `/monitor`, `/procedures`, and `/response` pages. Clearly distinguish currently working steps from stages still under development. A checkbox may track your rehearsal; it must not claim the actual incident was processed or approved.
4. Write `docs/demo/MANUAL_QA.md` with steps, expected result, actual result, commit tested, and pass/fail/not-tested. Cover loading the app, video upload, frame timeline/video seeking, backend disconnected state, and narrow/mobile layout. Later AI/response steps stay marked not tested until implemented.
5. Write `docs/DEMO_SCRIPT.md`: 20 seconds problem, 20 solution, 90 workflow, 30 architecture, 20 impact. Mention the assistant and human approval; label demo providers and simulated actions. Avoid fabricated accuracy/savings. Coordinate live detector wording with Sean.

Scope ends there. Do not edit global CSS, navigation, shared UI components, existing application routes, API types, backend, dependencies/lockfiles, root README, or detector. Record issues there for Yug or Sean. Optional within your scope: accessible progress checkboxes, clear empty instructions, responsive cards, keyboard-friendly links. No new packages needed.

## 3. Run locally (Windows PowerShell)

Prerequisites: Node.js compatible with the pinned Next.js (use Node 22 LTS), npm, Python 3.11+, Git. Read repo AGENTS.md/CLAUDE.md first. The frontend AGENTS.md also points to bundled Next.js docs under node_modules; read relevant docs after npm ci before coding.

Terminal A, from the repo root:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe -m app.seed.run
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If Python 3.11 is not installed, use an installed supported Python version (check `py -0p`) rather than changing system settings. Direct .venv executable calls avoid PowerShell activation-policy issues. Reuse an existing .venv when appropriate. Do not overwrite an existing .env.

Terminal B, from the repo root:

```powershell
cd frontend
npm ci
if (!(Test-Path .env.local)) { Copy-Item .env.example .env.local }
npm run dev
```

For macOS/Linux, use `python3 -m venv .venv`, `.venv/bin/python` in place of the Windows Python path, and copy missing env files with `cp`. Keep both servers running. Use `http://localhost:3000/demo-help`, `http://localhost:3000/monitor`, and `http://127.0.0.1:8000/docs`. Check `/api/health` on port 8000. If a port is occupied, identify the existing process; do not terminate unrelated work.

The frontend env needs `NEXT_PUBLIC_API_URL=http://localhost:8000`. For backend integration verification, set `NEXT_PUBLIC_DEMO_FALLBACK=false` in your local .env.local and restart Next.js; otherwise fallback data can hide a disconnected backend. Restore the desired local demo setting afterward. Later stages may add AI_PROVIDER; keep explicit demo providers for routine testing. No paid AI key is needed for your page.

## 4. Verify and see changes

With the frontend running, save and reload `/demo-help`. Inspect at desktop width and a narrow approximately 390px viewport. Check keyboard navigation, link destinations, readable contrast and text, no horizontal overflow, and no new browser-console errors. Do not claim browser testing if only static checks ran; ask the human to inspect if your AI has no browser access.

In a separate terminal under frontend:

```sh
npm run typecheck
npm run lint
npm run build
```

If concurrent dev/build processes interfere, stop only your own dev server and rerun the build, then restart it. Baseline backend check, from backend on Windows:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Report existing baseline failures separately. UI-only edits need frontend checks and visible inspection; backend edits belong to Yug. Use a small permitted MP4/MOV/WebM under current backend limits for the manual upload check. Keep videos, generated frames, reports, databases, env files and screenshots with private content out of commits.

## 5. Commit and share

At the start of each later session: status, fetch, then `git pull --ff-only` if your branch has an upstream. This syncs your branch only. Yug coordinates when to merge his integration baseline into yours.

From repo root after checks:

```sh
git branch --show-current
git diff
git add frontend/src/app/demo-help docs/demo docs/DEMO_SCRIPT.md
# Add frontend/src/components/demo-help separately only if you created it.
git diff --cached --stat
git diff --cached
git commit -m "Add demo help and rehearsal guide"
git push -u origin codex/abhinav-demo-support
```

Stage only existing paths you actually own. Send Yug the branch and commit, changed files, checks/results, and remaining issues. Request integration into Yug's CURRENT stage branch; do not blindly target main or an old stage. Do not force-push. GitHub Desktop can publish the branch manually if terminal auth fails. If still blocked, keep local commits and report the auth error; do not claim success.

## Paste this into your AI editor

> Work in my SafetyLens clone. Read docs/team/TEAM_PLAN.md and docs/team/ABHINAV_HANDOFF.md if present; otherwise use the handoff text I provide. Inspect repository instructions. Check status and fetch, then create or resume codex/abhinav-demo-support from origin/main (598eaf8 or newer). Preserve existing changes. I own only a new /demo-help route and its isolated components, docs/demo/, and docs/DEMO_SCRIPT.md. Implement the tasks in this handoff using existing dependencies and styling. Choose a clear accessible layout and useful wording. Start backend and frontend using the documented commands, inspect the page in a browser when available, run frontend typecheck/lint/build, and record actual QA results. Do not alter Yug's backend/shared frontend or Sean's detector. Label unimplemented stages accurately. Commit and push verified changes on my branch; if authentication fails, preserve commits and explain the manual login/publish steps. Finish with URLs, branch, commit, tests, and push status.
