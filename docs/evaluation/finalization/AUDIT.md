# Finalization audit — November 9

Baseline fetched main34404a0 includes PR12 merge8061daa and a README-only edit. Existing branches were inventoried; unrelated open PR9 (pitch deck on Sean branch) is preserved, not merged or overwritten. No uncommitted source existed. Baseline tests92 backend/66 detector, lint/typecheck were rerun.

Priority1 scientific validity: temporal cache decisions were duplicated, and no-pose handling could rearm a latched incident or count unseen time as upright recovery. One shared TemporalDecision now governs runtime/evaluation; regression tests exercise dropout/recovery and 18 actual-media replay comparisons. No training, model weights, operating point or final-test threshold tuning changes. Current metrics remain4/0/10/4; historical data is labeled published replay, not a new holdout.

Priority2 runtime resource safety: checkpoint loader checked a size limit after read_bytes, permitting unbounded initial allocation. It now reads at most2,000,001 bytes before validating hash/shape. Stable feature format and checkpoint hash are retained.

Priority3 dependency surface: unused shadcn generator shipped in runtime dependencies, pulling registry/morph packages. No application imports it; removal preserves generated components. Compatible lockfile fixes only; no force downgrades. Public advisory findings are recorded; development globbing risks are distinct from production dependencies.

Priority4 scientific scoring: association evaluator can count missing None identities as correct. Strict independent-label validation is required before freezing metrics; no empirical wearer accuracy is claimed.

Priority5 delivery: prior PostgreSQL verification used existing named volumes, not a wholly fresh installation. This phase verifies a new project with no existing containers/volumes, generated private secrets, zero default users and full documented Compose health, then actual inference/review/recovery.

Presentation: consolidate README into a two-minute overview while retaining original screenshots, architecture diagram, attribution and achievement. Freeze an authoritative source-indexed metrics document; move historical caveats to existing detailed documents. No fresh dataset is available under the current completed splits, so no new independent accuracy claim is justified.
