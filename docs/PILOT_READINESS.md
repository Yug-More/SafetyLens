# Controlled shadow-pilot readiness

**Current verdict: not workplace-ready and not yet accepted for an unattended pilot.** The local software workflow and controlled recovery are demonstrated, but broader detection recall is inadequate. PPE deployment is excluded. No workplace deployment, trained-personnel replacement, regulatory approval or safety certification occurred.

## Proposed acceptance protocol — not achieved metrics

Agree and freeze these engineering gates with the site's safety/privacy leads before collecting a pilot test set. The numeric proposals below are planning targets, not regulatory standards or proven SafetyLens outcomes:

- At least200 independently reviewed negative camera-hours covering shift/lighting changes and ordinary resting/bending activities. Proposed upper95% confidence bound on false alerts ≤.1 per camera-hour; evaluate each supported camera condition, not only a pooled average.
- At least100 independently annotated positive recordings/events using approved recordings and preapproved safe scenarios. Proposed recall lower95% bound ≥.90. Do not ask workers to perform dangerous falls. Use blinded annotation and preserve disagreement/misses.
- Subject, session and recording separation between development and final evaluation; paired camera views remain grouped. The current unknown-subject public benchmark does not satisfy this gate.
- Proposed p95 capture-to-operator-notification latency ≤10s on the agreed local hardware/network, measured with synchronized timestamps and all missed/undelivered events accounted for. Offline FPS/detected-only video delay cannot satisfy it.
- Zero silently lost acknowledged evidence in a predeclared interruption suite; no duplicate incident per same event UUID; recovery after backend/database restart; bounded queues and explicit capacity failure. Include an outage long enough to test storage/backpressure, not only a brief disconnect.
- Pass site access/retention/privacy review; verify encrypted transport and backup restoration with keys; zero unintended real external actions. Independently approve the operator escalation process.

A failure is recorded, investigated on development data and followed by a **new** frozen evaluation set. Do not retune repeatedly against these acceptance clips. No current public benchmark result establishes these gates.

## Supported conditions versus unknowns

Tested reference hardware is Apple M2 Pro/16GiB RAM, Python3.12, CPU MediaPipe0.10.21, local OpenCV and isolated PostgreSQL17/Next containers. No minimum viable CPU/RAM lower bound has been established. Provision adequate disk for container builds, original+playback evidence, outbox and backups; a constrained build previously exhausted the host. Benchmark on the actual target machine before selecting camera count.

Current verified vision evidence uses recorded public scenes and explicit RGB-region calibration; composite depth/RGB layouts must be calibrated rather than fed as one view. Ceiling/side views, short tails, partial bodies, low light, additional seated people and intentional reclining expose failures. No approved illumination/distance/resolution range or stable crowd identity guarantee exists. Four repeated recorded streams are not four independently validated cameras.

## Installation and camera placement

Follow README, DEPLOYMENT_VERIFICATION.md and CAMERA_PIPELINE.md. Use a dedicated installation with administrator bootstrap, protected private secrets and camera-scoped device access. For any nonlocal use, validate HTTPS and secure cookies. Configure camera source on the edge worker, sample policy/recording windows and storage bounds. Keep useful full-body/context visibility and explicitly label excluded/unsupported views; test ordinary activity before treating any alert as operationally useful. An empty/offline camera is not evidence that no incident occurred.

Physical camera permissions, RTSP hardware/reconnection and sustained fleet behavior must be tested on site. The controlled MJPEG disconnect test is useful software evidence but not a hardware sign-off. Local PPE remains disabled; historical/multimodal review should not be presented as validated continuous compliance measurement.

## Operators, privacy and failure handling

Train authorized operators to check evidence, interpret uncertainty, confirm/reject/request information, assign/acknowledge notes, inspect actual SOP citations and approve only selected simulated actions. Rehearse stale-version conflicts and session reauthentication. Maintain existing trained personnel and site emergency procedures independently of SafetyLens. Unknown injuries and identities must not be inferred from model output.

Obtain the site's privacy/worker consultation and appropriate legal review; minimize camera coverage and retained media, restrict exports and avoid private areas. No biometric recognition or productivity surveillance is implemented. Configure retention, preview expiration candidates and audit deletion/export. Back up database/media consistently and retain the encryption key securely; rehearse restoration to a separate environment.

Monitor heartbeat/stale status, queue backlog/capacity, ingestion errors, storage and review burden. If the backend is unavailable, preserve outbox evidence and follow the site's independent response process. If storage fills or a camera/model is inconclusive, escalate the system failure rather than interpreting it as safety clearance. Stop the shadow evaluation if operator workload, missed-event risk, privacy or evidence integrity exceeds the agreed limits.

## Current classification

Working local prototype: **verified**. Evaluated experimental detector: **verified with poor broader recall and unresolved false alerts**. Controlled shadow-pilot candidate: **conditional; gates above not met**. Production workplace system or certified safety equipment: **not established**. No meaningful real-world readiness assessment can omit the broader low-recall result in DETECTION_VALIDATION.md.
