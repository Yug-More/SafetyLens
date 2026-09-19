# SafetyLens documentation

Start with the [project README](../README.md) for current capabilities and setup.

## Current guides

- [Backend](../backend/README.md): providers, ingestion API, persistence, and demo reset.
- [Frontend](../frontend/README.md): dashboard configuration and commands.
- [Detector](../detector/README.md): live camera input, recordings, state transitions, and evidence files.
- [Demo script](DEMO_SCRIPT.md): fall-focused presentation and honest provider boundaries.
- [Manual QA](demo/MANUAL_QA.md): rehearsal checklist.
- [Showcase assets](assets/demo/): original normal-standing and fall-detected screenshots.

## Retained design and team context

The files under `team/` preserve the original task split, staged build plans, detector contract, and fall-only release notes. Stage numbers and assignments describe development history; they are not the current feature inventory. In particular, the later PPE workflow is implemented even though the original release plan focused on falls.

Keep these references for future work, but use the component guides and current code for setup. Expansion priorities include multi-person tracking, reliable camera ingestion, automatic evidence delivery, retention controls, and deployment hardening. The existing provider abstractions, PPE policies, ingestion API, and demo fixtures support that work and remain in the repository.
