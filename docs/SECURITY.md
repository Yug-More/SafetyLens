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
