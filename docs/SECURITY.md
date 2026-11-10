# Security and privacy

## Implemented controls

Authentication defaults on. Bootstrap a local administrator with `python -m app.manage create-user --username YOUR_NAME` from backend; the password is read interactively and must have 12+ characters. There is no default credential. Passwords use salted scrypt; session tokens have 256 bits of entropy and are hashed in the database. Session cookies are HttpOnly/SameSite=Strict; enable Secure cookies behind HTTPS. Sessions expire and are revoked by logout or role/deactivation changes. Failed logins are rate-limited per direct client IP in a database-backed 15-minute window; proxy-aware identity and distributed rate-limit hardening remain deployment work.

Browser mutations require session-specific CSRF tokens and allowed Origin. Roles: viewer reads; operator uploads/reviews; manager approves, executes simulations, retries, coordinates incidents; administrator configures cameras/users/retention/reset access. Review and approval names come from the authenticated actor. Retry rechecks current confirmation and original active approval. Cross-incident report/plan linking is rejected. Device credentials are separate from browser sessions and camera-scoped through an allowlist.

Camera sources are encrypted with Fernet and are not returned by inventory APIs. Admins/scoped devices can retrieve sources; network access and device storage must be secured separately. Evidence/report downloads require authentication. Video/procedure uploads have byte limits, type checks, randomized filenames and contained paths. CSV export escapes spreadsheet formula prefixes. Database/media encryption at rest and malware scanning are not implemented by the application.

## Audit and privacy limits

Application audit records include login, user creation/access changes, reviews, plans, approvals, simulated actions, reports, CSV exports and incident coordination. Camera configuration emits resumable change events; complete compliance-grade configuration auditing is not claimed. Audit tables are not cryptographically immutable or certified. Authenticated installations disable broad demo reset to avoid deleting decision history. Change-event replay is retained for 30 days independently of audit history.

Video is sensitive. Optional external vision analysis transmits selected images to the configured provider. Obtain appropriate authorization and retention agreements before using workplace footage. No face recognition, identity inference or productivity scoring is implemented. Face blurring is not implemented. All users belong to one trusted installation; there is no multi-organization isolation.

## Deployment requirements

`ENVIRONMENT=production` refuses startup unless authentication and Secure cookies are enabled. Terminate TLS with a reviewed proxy; use same-site frontend/API origins. Supply secrets outside Git. Do not expose the API or camera networks publicly without network controls. Back up the database and camera encryption key. Keep report/evidence volumes access-controlled. The local Compose profile uses HTTP for development and is not a production certification.

External notifications, medical calls and physical controls remain disabled: all action execution is simulated. No industrial safety, medical, legal or regulatory guarantee is made. The small external detection experiment shows low recall; trained personnel and existing safety systems remain necessary.

## Final continuation review

The continued model-backed browser test exercises actual scoped device delivery, notification, human approval, simulated execution, audit and PDF access. New Docker context exclusions prevent accidental inclusion of private environment files and host dependencies. Local role/CSRF/session/device tests remain passing; these checks are not penetration testing or organization isolation. New pose-region input is normalized, finite and nonempty. Fixed ONNX float input dimensions are validated rather than silently assuming a compatible export. Public dataset images and model weights remain outside Git. Reference PPE model deployment is explicitly excluded pending license resolution and useful labeled performance. See FINAL_RELEASE_REPORT.md for current evidence and deployment limits.

## Final hardening evidence

Current verified scope, commands and limitations are recorded in [FINAL_RELEASE_REPORT.md](FINAL_RELEASE_REPORT.md), [DEPLOYMENT_VERIFICATION.md](DEPLOYMENT_VERIFICATION.md), [SECURITY_REVIEW.md](SECURITY_REVIEW.md) and [PERFORMANCE_REPORT.md](PERFORMANCE_REPORT.md). These supersede earlier unverified frontend/PostgreSQL-17 status; they do not establish workplace readiness.

## November 8 research-phase controls

The pure ASGI `BodyBudgetMiddleware` counts actual received bytes before multipart spooling, with early Content-Length rejection and a 110MiB default for recognized media-upload routes only. Spoofing a multipart content type on metadata routes does not obtain the media allowance. Other metadata is limited to256KiB; detector snapshots to at most2MiB. `MAX_REQUEST_SIZE_MB` is configurable in settings/Compose. This does not provide rate limiting, upload antivirus, decode sandboxing, connection limits or a production HTTPS proxy.

Provider metadata now appears as JSON descriptive data under explicit untrusted-content instructions; frame paths/URLs are not interpolated as remote-fetch instructions. Existing provider output checks and server approval remain. Untrusted remote exception content is neither logged nor exposed through chained public errors; a regression checks both logs and formatted traceback. These tests do not measure prompt-injection resistance of a live paid model. Retrieved SOPs remain untrusted text; deterministic planning has no external execution authority, and human approval is independently enforced.

PPE context preview/configuration is administrator-only, with role and CSRF checks; viewers may inspect class gates. Unknown context and missing visibility remain unknown. Appearance observations cannot bypass per-class deployment gates or certify protective equipment. No worker identity is inferred from operational-role fields. All categories remain disabled for deployment.

Research checkpoint inference uses hash-pinned bounded JSON with numeric/shape validation. The optional export tool loads an official, explicitly hashed PyTorch research checkpoint; arbitrary pickle files are unsupported. No trained weights, source media, private credentials, QA dumps or employee footage are committed. Camera source timeouts and a one-slot latest-frame buffer reduce stale-frame growth; native backend guarantees and physical RTSP operation remain unverified.

The installation still shares authorized evidence across its users by role. It does not implement organization tenancy or per-user ownership isolation, SSO/MFA, an immutable audit ledger or distributed exactly-once actions. A proxy/service admission policy and representative security testing remain requirements before nonlocal operational deployment. No external consequential action was added.

New automated `ppe_noncompliance` detector ingestion is rejected while all visual gates are closed, even if a device bypasses the normal worker/configuration controls. Existing UUID acknowledgements remain retryable. Configured demos, human review and offline diagnostics are separate paths, not qualified live PPE deployment.

## Final release advisory and allocation review

The exact final lockfile audit reports zero known vulnerabilities across52 pinned Python packages, zero frontend production advisories and seven moderate development-tool advisories, with no high/critical findings. `npm audit fix --force` would require incompatible changes and was not used. The remaining glob-amplification findings apply to trusted-project lint tooling; they are not exposed as an application API. This is a public-advisory snapshot, not a penetration test or a vulnerability-free guarantee. Reports and scope are in `evaluation/finalization/`.

The shadcn generator tree is no longer a runtime dependency. Its required stylesheet remains unmodified with MIT license/provenance. Temporal checkpoint reads are capped before parsing/allocation, and independent association labels cannot use missing/duplicate IDs to manufacture accuracy. No role, evidence, approval or deployment gate was weakened. Metrics/source drift is now a CI failure.
