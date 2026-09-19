# SafetyLens Three-Minute Demo Script

This script describes the current prototype honestly. Use only consented or licensed demo
video. Do not claim measured accuracy, savings, sent alerts, or completed emergency actions
unless the integrated build demonstrates them.

## 0:00–0:20 — Problem

“Workplaces already have cameras, but most footage is reviewed after an incident. A supervisor
may need to find a clip, understand what happened, locate the right safety procedure, and
coordinate a response under pressure. SafetyLens is designed to make that review path faster,
more explainable, and human-controlled.”

## 0:20–0:40 — Solution

“SafetyLens connects an existing camera workflow to an assistant for evidence review, procedure
guidance, and proposed next steps. The assistant supports the supervisor; it does not replace
emergency services or make consequential decisions on its own.”

## 0:40–2:10 — Current workflow

1. “This is the **Live Monitor**. For this rehearsal, we use a short prerecorded demo clip from
   Camera 04 in Loading Zone B.”
2. “I upload the clip. In the current Stage 3 build, the backend validates it, stores it locally
   for the demo, reads video metadata, and samples representative frames.”
3. “When the processing job is ready, we can replay the clip and inspect the frame timeline.
   These are evidence candidates for a reviewer—not a confirmed incident verdict.”
4. “Next, the **Procedures** page shows the seeded safety-procedure library. Matching a procedure
   to the uploaded video is planned for a later stage, so we do not present this as automated
   retrieval today.”
5. “The **Response Center** illustrates the intended supervisor experience: review evidence,
   consider a recommended plan, and approve or reject it. Its provider is a seeded demo data
   source in this build; approval is simulated. No alerts, tickets, equipment controls, or
   emergency actions are actually sent.”

## 2:10–2:40 — Architecture

“The current implementation is a Next.js operations console connected to a FastAPI service with
SQLite metadata and OpenCV video processing. The future path adds multimodal verification,
cited procedure retrieval, and an auditable simulated-action workflow. Keeping those stages
explicit lets us demonstrate useful groundwork without overstating automation.”

## 2:40–3:00 — Impact

“SafetyLens aims to turn passive footage into a structured, review-ready safety workflow. The
value is not an unattended decision—it is helping the right person see relevant evidence,
understand what still needs verification, and stay in control of the response.”

## Presenter reminders

- State the video source and consent status if asked.
- Say “candidate frame” rather than “detected fall” for the current Stage 3 pipeline.
- Say “seeded demo provider” and “simulated approval” when showing the Response Center.
- If a live upload fails, explain the API connection state rather than claiming the demo completed.
