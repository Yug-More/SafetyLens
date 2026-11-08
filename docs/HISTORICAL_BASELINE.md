# Historical baseline

Original SafetyLens is preserved at Git commit `178f0f8a77f2f6c664822fe6ef09f62ff6342f15`; no history rewritten. Original screenshots, team handoffs, tests, demo providers, and fall state machine are retained. The original model is pretrained MediaPipe; temporal rules are custom logic, not trained weights. PPE demo choices are not pixel detection. OpenAI vision is optional; original OpenAI planner delegates to deterministic templates. Actions are simulated.

Team ownership documented in `team/TEAM_PLAN.md`: Sean — detector; Yug — backend/main application integration; Abhinav — demo support. New enhancement commits do not reattribute historical work.

## Original measurement evidence

Fall-only release notes describe staged tuning on the same person/setup at 8/12/15 FPS. This is not held-out accuracy. No independent detector accuracy, SLA, deployed fleet, or response-time reduction was verified. Dashboard constants are not benchmarks. The enhancement starts with 44 detector and 68 backend tests passing on November 7, 2026; these establish regression behavior, not detection performance.

## Enhanced SafetyLens

See CHANGELOG.md and DETECTION_EVALUATION.md for actual additions and validation. Legacy configuration remains available. New experimental adapters are never represented as evaluated detectors without supplied weights and held-out data. Original demonstration remains explicitly simulated.
