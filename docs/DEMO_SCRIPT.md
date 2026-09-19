# SafetyLens: three-minute fall-only demo

## 0:00–0:25 — One problem

“A camera can record someone falling without helping the reviewer decide what to do next.
We focus on one workflow: flag a possible fall, show the evidence, and help a supervisor
follow a documented response.”

## 0:25–1:00 — Real detector, narrow claim

“This is a consented staged fall. A local pose model feeds a state machine that checks
movement and sustained down posture before emitting a possible-person-down event. Here
are its timestamp, signals and transitions. Walking out of frame and sitting are our initial
negative examples—not proof of general accuracy.”

Show the detector result beside the recording; import JSON and matching video in Live Monitor.
Precomputed results are fine: say they were precomputed. Upload itself does not run detection.

## 1:00–1:35 — Review and cited guidance

“The event brings evidence into the workspace. Default Demo AI is scripted for presentation;
it does not actually inspect these frames. The real detector is separate. We retrieve the
seeded fall procedure and generate a cited proposed plan. The reviewer can inspect the source
instead of trusting an unexplained recommendation.”

Choose the matching analysis, retrieve SOP-FALL-4.2 and show a citation. Describe real AI
instead only if a real provider has genuinely been configured and tested.

## 1:35–2:25 — The assistant's value

“Detection alone leaves someone to locate procedures, decide the response, and document
what happened. This assistant brings those steps together. A human selects and approves
actions. Execution here is simulated: no notification or emergency call is sent.”

Approve plan actions, run simulation, show audit, generate/download PDF. Approval/audit/report
records are real application artifacts; external actions are not real.

## 2:25–3:00 — Boundaries and close

“We connect local fall-candidate detection to evidence, cited guidance, human review and an
auditable record. We used a handful of staged clips from one setup for tuning, so we do not
claim measured accuracy or lives saved. Next we would test new camera angles and false
positives. Today the focus is a clear fall-response workflow.”

## Rehearsal and fallback

- Prepare real detector JSON and consented video locally; do not depend on Camo finishing.
- Test API, retrieval, approval, simulated execution and PDF download before presenting.
- If import fails, ordinary upload demonstrates downstream workflow only; disclose that.
- If API fails, use explicitly labeled rehearsal screenshots rather than claiming completion.
- No injury diagnosis, production monitoring, automated dispatch or other-hazard detection claims.
