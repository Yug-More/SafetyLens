# Security review — final hardening

Scope: code review, automated controls, actual local Compose/PostgreSQL17 workflow and failure injection. This is not an external penetration test, compliance attestation or safety certification. Threat boundaries: browser/operator sessions, untrusted uploaded media, edge-device tokens, privileged camera-source configuration, database/evidence volumes and optional paid AI services. A single installation trusts its administrators; tenant isolation is not implemented.

## Confirmed fixes and evidence

- **Device information exposure:** bearer authentication previously matched the event path without checking its HTTP method, allowing a device to list detector records. `auth.authorize` now accepts only the intended method/path pairs. `test_device_cannot_enumerate_events_or_rebind_an_event_id` proves listing is denied.
- **Idempotency rebinding:** a reused UUID could reuse another camera/source's mapping. `ingest_detector_event` now rejects camera/source/type conflicts and conflicting declared content hashes with409. Device scope remains checked before ingestion.
- **Evidence transfer integrity:** the durable outbox attaches SHA-256; ingestion verifies actual stored bytes and rejects mismatches. The real Compose event's backend/original-clip hash matched. Hashes do not prove a compromised device's observations are truthful, nor constitute a certified evidence chain.
- **Restart data integrity:** default demo seeding rewrote camera/operator state and tried deleting SOP chunks referenced by retrievals. The actual PostgreSQL restart failed. Normal seeding now preserves initialized records; explicit confirmed demo reset retains separate behavior. Regression and real restart verified stable records/citations. Completed media processing is idempotent and same-process retry/recovery uses per-video locks.
- **Concurrent incident coordination:** first-write initialization could race before compare-and-swap. Insert conflicts now return409; SQL version checks protect updates. Two actual authenticated roles submitted one version concurrently:200/409. This does not prove distributed exactly-once action execution.
- **Local exposure:** documented HTTP profile now binds frontend/API ports to127.0.0.1. PostgreSQL is not published on the host. Docker contexts exclude private environment files, local media and host dependencies. Containers use non-root runtime users.
- **Unsafe model activation:** camera API and worker reject local PPE deployment pending a useful license-reviewed model. Research adapters cannot silently become production compliance monitors.

Sources: [auth.py](../backend/app/services/auth.py), [detector_ingestion.py](../backend/app/services/detector_ingestion.py), [delivery.py](../detector/src/safetylens_detector/delivery.py), [platform.py](../backend/app/api/routes/platform.py), [seed_data.py](../backend/app/seed/seed_data.py), [recovery.py](../backend/app/services/recovery.py), [test_platform.py](../backend/tests/test_platform.py), and `evaluation/hardening/compose-verification.json`.

## Retained controls exercised

Opaque hashed sessions, scrypt passwords, strict HttpOnly cookies, CSRF/origin checks, session expiry/logout, four server-enforced roles, camera-scoped device requests, encrypted camera source strings, protected evidence/PDF downloads, bounded upload/path validation and retention safeguards remain covered by backend/browser tests. Actual approval and execution remain separate. The only action executor is simulated; no emergency dispatch, messaging account or physical equipment is controlled. There is no facial recognition or employee productivity scoring.

The final Docker browser used real local-CV findings with unknown/calibration-limited confidence and preserved human confirmation. Invalid device scope/hash and viewer mutations are rejected. The API's optional legacy hashless ingest contract remains for historical compatibility; new outbox deliveries include hashes. Sensitive private dumps are not committed.

## Recovery and backup evidence

Local persisted detector jobs are snapshotted before new requests at startup and recovered in a bounded single-process background path. A regression stops after actual media/storage commit, then runs recovery and verifies a local-CV incident; reprocessing a completed job preserves frame IDs. The real container outage test separately verifies durable outbox recovery and duplicate mapping reuse. Startup recovery is not a distributed lease/task queue; multiple API replicas are unsupported by this guarantee.

PostgreSQL17 restart preserved sessions/evidence mapping. A private pg_dump was restored to a newly created verification database. A separate88-file media snapshot restored to a new volume with all SHA hashes intact; its archive was0600. These are quiescent component checks, not a coordinated point-in-time/offsite disaster-recovery exercise. Camera encryption keys remain separately required for restoring encrypted source configuration. Script outputs omit passwords/tokens; dumps, private QA credentials and archives stay outside Git.

## Unresolved threats and release limits

- Real HTTPS/proxy/secure-cookie deployment was not exercised. Production configuration refuses insecure cookies/auth disabled, but that is not TLS validation.
- No SSO/MFA/password recovery, per-organization isolation or per-device credential issuance. The configured device token is shared within its configured camera scope; compromise requires rotation.
- No independently tamper-proof audit ledger, encrypted evidence-at-rest/offsite backup policy, formal access attestation or complete browser CSP/penetration review.
- Administrative source configuration intentionally gives the trusted edge worker local/network camera access. Network segmentation/egress controls remain deployment responsibilities; do not treat administrator access as a tenant sandbox.
- Login throttling is local persisted per-IP control, not comprehensive distributed abuse protection. Trusted reverse-proxy behavior requires validation.
- External-provider prompts/schema validation cannot guarantee hallucination absence. No live paid-provider test was authorized by available credentials in this phase.
- The recorded npm audit still has13 findings (2 low,11 moderate). No high/critical finding in that snapshot is not proof that the platform is vulnerability-free.
- No distributed execution transaction/lease guarantee or independent audit of every authorization path. Real consequential integrations must remain disabled.

These limits prevent a production-security or workplace-readiness claim. The supported verified profile is a local authenticated experimental system with controlled simulated response.

### Duplicate-upload liveness boundary

`detector_ingestion.ingest_detector_event` serializes same-UUID ingestion in one process with a weakly retained async lock, avoiding an event-loop/transaction wait during spooled file reads. A real concurrent-upload probe verified two 202 responses sharing one asset. Database uniqueness remains the persistent constraint; this is not a distributed lock. Multipart parsing, ingress request-size limits and rate limiting still require deployment-level controls; application upload checks alone do not establish denial-of-service resistance.
