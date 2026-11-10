# Graduate application presentation

These summaries describe an experimental project, not a certified or deployed workplace system. Word counts below use whitespace-separated words. Award attribution and genuine team history remain in the root README and historical documents.

## 75-word project summary

SafetyLens connects camera-based safety observations to preserved evidence, incident review, retrieved procedures, human approval, and auditable simulated response. The project combines MediaPipe pose estimation, temporal classification, ONNX object detection, FastAPI, PostgreSQL, and a Next.js operator console. Its strongest research contribution is reproducible evaluation with explicit uncertainty, including correction of mislabeled benchmark categories. The team reported first place at The Executable World Hackathon and a $25,000 prize. Workplace reliability remains unestablished. These limitations shape ongoing research.

## 150-word technical summary

SafetyLens is an experimental computer vision and intelligent software platform that connects local detection to evidence preservation, cited procedures, human-supervised incident response, and reporting. A separate camera worker performs MediaPipe pose inference, maintains per-person temporal state, and delivers checksum-verified clips through a persistent retry outbox. FastAPI services enforce authentication, device scope, versioned incident updates, and human approval; PostgreSQL stores workflows and audit records, while Next.js provides evidence review and operational interfaces. A causal temporal learning pipeline compares regularized linear classification with a small neural model using explicit recording splits and validation-only selection. Fresh evaluation exposed unacceptable false alarms despite improved sensitivity, preventing default promotion. Multi-class ONNX PPE research independently verified semantic labels against original annotations and separates object appearance from protective ratings. Eight policy categories remain deployment-disabled. Actual detector-to-PDF integration and controlled recovery were verified locally; physical production camera fleets, independent wearer accuracy, and representative workplace safety validation remain unresolved.

## 250-word research-oriented summary

SafetyLens explores a question in applied artificial intelligence: how can uncertain visual observations become useful, reviewable evidence without surrendering human authority? The platform joins local camera inference, protected evidence storage, incident interpretation, procedure retrieval, explicit approval, simulated response, and audit reporting. Its architecture separates computer vision findings, optional multimodal interpretation, configured demonstrations, and human decisions rather than treating their outputs as interchangeable facts.

The fall-detection investigation progressed beyond threshold adjustment. A reproducible learning pipeline extracted causal pose geometry and motion summaries, fitted normalization on training recordings, and compared regularized linear and neural temporal classifiers using validation-only model selection. Fresh recordings revealed that greater sensitivity came with excessive false alerts. Keeping the candidate experimental demonstrates why held-out evaluation and negative exposure matter more than an attractive recall statistic. Subject and session identities remain unknown, limiting generalization claims.

A second investigation uncovered a benchmark provenance failure. Numeric PPE categories in a third-party dataset mirror had been renumbered, invalidating earlier equipment metrics. Matching 1,172 rectangles against independent publisher annotations recovered semantics without consulting predictions. Corrected multi-class evaluation distinguished visible glasses, shoes, and masks from verified protective equipment. Person-specific association abstains on ambiguity, and missing visibility remains unknown.

The systems work makes these research findings operationally inspectable: durable authenticated delivery, evidence checksums, bounded stream buffering, PostgreSQL recovery, contextual policies, and browser workflows connect actual model events to human review and reports. SafetyLens offers a foundation for studying reliable multimodal systems, while openly acknowledging unresolved false alarms, licensing constraints, wearer validation, and industrial deployment requirements.

## Three résumé candidates

- Built a causal pose-learning pipeline with training-only normalization, recording-aware train/validation/test splits and frozen operating-point selection; evaluated linear and neural temporal classifiers and quantified the missed-event/false-alert tradeoff on fresh footage.
- Diagnosed semantic category corruption in a PPE benchmark mirror, independently matched 1,172 boxes to original annotations, and corrected nine-class ONNX evaluation while preserving uncertainty in person-specific equipment review.
- Integrated authenticated CV evidence delivery, checksum/idempotency safeguards, cited SOP retrieval and human-approved simulated response in a FastAPI/Next.js/PostgreSQL platform; verified actual-model browser workflows, outages and isolated restoration.

Use these only for work you can explain and substantiate personally. They intentionally avoid presenting four-positive recall as general accuracy, object AP as wearer compliance, or simulations as external deployment.

## Individual and team contributions

The historical [Yug handoff](team/YUG_HANDOFF.md) assigns Yug the main backend, database, uploaded-video/AI pipeline, retrieval/planning, approval/execution/reporting, shared frontend and deployment. It assigns Sean the detector, live metrics/state machine/evidence buffering, and Abhinav the demo-help interface and demo guide. Original contributor acknowledgments and Git attribution are preserved.

This phase adds learned temporal research, label-provenance correction, multi-class offline evaluation, explicit PPE/context gates, stream backpressure and ingress/provider defenses under the requested Yug-More commit identity. Commit identity and task ownership do not independently prove who personally designed or implemented each line. Before using first-person admissions claims, confirm which design, debugging, experiments and integration you personally performed; credit inherited/team work explicitly. No unsupported team-leadership role or sole-authorship claim is supplied.

## Verified metrics and useful techniques

Current references: [fall evaluation](FALL_DETECTION_EVALUATION.md), [PPE evaluation](PPE_EVALUATION.md), [final validation](FINAL_VALIDATION_REPORT.md).

- Frozen learned fall test: TP4/FN0/FP10/TN4; F1 .4444, precision .2857. Four positive recordings and excessive false alerts prevent a reliable high-recall claim.
- Corrected 100-image appearance diagnostic: person recall .8178/AP50 .7846; helmet recall .4250/AP50 .3587; vest recall .7667/AP50 .6121. Training overlap is unknown; these do not establish protective rating or wearer compliance.
- Independent semantic verification: all 1,172 source/mirror rectangles matched; no unmatched boxes. Historical erroneous equipment metrics are explicitly withdrawn.
- Real model-to-report integration, role/approval controls, PostgreSQL migration/recovery, and browser tests are engineering evidence; no coverage percentage or industrial deployment is inferred.

Relevant techniques include causal temporal feature extraction, regularized classification, neural-model comparison, validation-only operating points, onset matching, uncertainty intervals, dataset provenance, ONNX export parity, class NMS, geometric association/abstention, bounded stream buffers, durable retries, API authorization, optimistic concurrency, lexical retrieval/citation snapshots and human oversight.

## Readiness for graduate applications

The project can substantiate applied computer vision, AI systems integration and reliability reasoning when presented with clear personal ownership and reproducible evidence. Its strongest research experiences are the rejected sensitivity improvement, independently verified label correction, and end-to-end recovery/oversight design. It does not establish publications, customer adoption, production readiness, certification or research novelty against the literature. Admissions claims should emphasize methods, engineering decisions and evidence rather than inflated accuracy.

## Faculty interview questions and evidence-based answers

**Why did you keep the simplest learned model?** The compact linear model outperformed the fixed32-unit neural alternative on validation. Fresh test specificity was poor, so neither an attractive recall value nor extra complexity justified default promotion. The operating point was not retuned to the published test.

**How did you establish that PPE scores were wrong?** Original publisher annotations were independently matched to1,172 mirror rectangles; all matches were geometrically consistent and recovered the class mapping without consulting predictions. Historical equipment scores were withdrawn and re-scored from preserved predictions.

**How do models obtain authority to act?** They do not authorize actions. Authenticated role checks, incident confirmation and selective human approval are enforced independently in backend workflows. Cited SOP text and optional multimodal interpretation remain decision support; external execution is simulated.

**What makes the final results reproducible?** A shared runtime/evaluation temporal decision component, exact model/data hashes, versioned raw artifacts, fixed operating point, fresh-volume deployment verification and a machine-checkable metrics freeze. Replay of published test data is labeled replay, not a new holdout. See FINAL_PROJECT_METRICS.md.
