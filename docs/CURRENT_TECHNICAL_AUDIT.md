# Research baseline audit

Latest main af081c0, dedicated branch codex/temporal-research-ppe-policy. Inventory: 330 text source/config/test/document artifacts; Python definitions parsed; hashes retained outside repository. Existing architecture, original team ownership, implementation paths, dependencies, migrations, policies, API contracts and reports reviewed. Original award and screenshots retained.

Baseline independently rerun: backend 84 passed13.75s; detector 58 passed.081s; frontend lint/typecheck passed; actual-model browser suite8 passed (1.1m). Existing public benchmark data remains historical, not a fresh holdout.

Highest impact: (1) low fall recall and short post-fall tails/pose loss; (2) no useful validated person/PPE replacement; (3) unsupported PPE categories lack explicit policy/gate representation; (4) request-body limits occur after multipart parser, creating resource risk; (5) provider text metadata is interpolated as instructions rather than structured untrusted data; (6) camera preview refresh may overlap and show stale requests; (7) architecture/deployment statements disagree across historical/current documents. Multi-person IDs are ephemeral, no biometric identity. OpenAI integration is implemented but live paid service unverified; plans are deterministic and executions simulated. No tenancy; evidence shared only within the authenticated single installation according to role, not per-user ownership.

Chosen work: causal learned temporal comparison with recording-aware split and safe JSON checkpoint; per-class PPE policy/gate/status and context resolution with conservative unknown semantics; ingress byte budget; provider metadata boundary; bounded camera preview polling; real integration reruns. No claim to solve representative deployment quality through more tests. PPO/TCN/transformer complexity without data would not establish validity. Deployment default requires stronger evidence than a tiny test. Original docs/evaluation and contributor history preserved.

## Confirmed findings after implementation

- Critical scientific error: the mirror's numeric equipment labels did not retain publisher semantics. Independently matched 1,172 source rectangles; all consistent, none unmatched. Prior equipment scores withdrawn and original predictions replayed with corrected labels. This supersedes the audit's initial assumption that every poor PPE result was a model failure.
- Learned temporal sensitivity improved but fresh specificity collapsed; retained opt-in research status rather than promoting against an unsuitable benchmark.
- Camera/zone PPE policy updates previously left the legacy zone label stale; now synchronized. Seeded camera context preview initially ignored stored requirements when no enhanced config existed; fixed with a real API regression.
- Multipart checks happened after parser spooling; a route-aware ASGI byte budget now limits actual incoming bytes and rejects oversized/spoofed metadata early.
- Provider raw exceptions could expose untrusted remote text in logs/tracebacks; redacted and regression-tested. Metadata boundaries improved, without claiming complete live-model prompt-injection protection.
- Preview polling could overlap; sequential timeout-bounded polling now prevents this. Network frames could become stale in capture buffering; the single-slot reader replaces/counts stale frames and uses explicit native timeout options. Actual controlled MJPEG reconnection passed; no hardware RTSP claim.

Final evidence and unresolved limits are in FINAL_VALIDATION_REPORT.md. No distributed recovery, tenant isolation, protective-rating validation or industrial safety certification was added.
