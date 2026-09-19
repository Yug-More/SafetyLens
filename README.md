# SafetyLens

### See danger. Trigger action.

SafetyLens is an AI-powered workplace safety agent that transforms existing security cameras into proactive incident-response systems.

It continuously monitors camera feeds using lightweight computer vision. When a potential incident occurs, SafetyLens captures the relevant moment, uses multimodal AI to understand what happened, retrieves the appropriate company safety procedure, and recommends real-world actions—with human approval for critical decisions.

Built for **The Executable World: A Full-Stack AI Hackathon**.

---

## The Problem

Most workplaces already have security cameras, but these cameras are primarily passive recording devices.

When an incident occurs:

- Someone must be watching the correct camera at the correct time.
- Dangerous situations may remain unnoticed for several minutes.
- Employees must manually locate the correct safety procedure.
- Supervisors must contact the appropriate responders.
- Incident reports must be written manually.
- Footage is often reviewed only after the damage has occurred.

Running a powerful multimodal AI model continuously across every camera would also be expensive, slow, privacy-intensive, and difficult to scale.

SafetyLens bridges the gap between **seeing an incident** and **taking the correct action**.

---

## Our Solution

SafetyLens connects workplace cameras, AI reasoning, company safety procedures, and response tools into one intelligent workflow.

The system can:

- Detect a possible workplace incident
- Capture the relevant video evidence
- Determine what happened
- Evaluate severity and confidence
- Retrieve the relevant company procedure
- Recommend the correct response
- Request human approval
- Execute approved actions
- Generate a complete incident report
- Maintain an auditable history of every decision

SafetyLens transforms cameras from passive recording devices into proactive safety agents.

---

## Workflow

```mermaid
flowchart LR
    A[Camera Feed] --> B[Incident Detection]
    B --> C[AI Verification]
    C --> D[Safety Procedure Retrieval]
    D --> E[Human Approval]
    E --> F[Action Execution]
    F --> G[Incident Report]
```

This event-triggered architecture keeps routine footage local and activates advanced AI only when necessary, making SafetyLens more affordable, private, and scalable.

---

## Current Stage (Stage 5)

Stage 5 adds company procedure ingestion, deterministic local retrieval with verified citations, and grounded response-plan generation on top of Stage 4 analysis.

### Architecture

```text
completed analysis
   → lexical retrieval over stored procedure chunks
   → verified citations (exact stored text)
   → Demo/optional planner → ResponsePlan (recommendations only)
```

### Capabilities available now

- Stages 1–4 preserved (dashboard, upload, frames, multimodal analysis, human analysis review)
- Procedure upload: PDF, TXT, Markdown with size/path safeguards
- Deterministic chunking with section/page metadata when available
- Local lexical retrieval (no paid API required); method labeled in responses
- Grounded response plans where every policy action cites verified chunks
- `insufficient_policy` when evidence is missing (no invented policy claims)
- UI labeling: Demo vs real planner; **Recommended, not executed**

### Stage 5 limitations

- No human approval of response actions (Stage 6)
- No action execution, alerts, tickets, or emergency contact (Stage 6)
- No PDF incident reports or full audit execution trail (Stage 6)
- Live detector integration remains separate (Sean)
- Sample SOP text is demonstration content, not legal advice

---

## How It Works (Full Product Vision)

SafetyLens uses a two-stage AI pipeline.

### Continuous Edge Monitoring

A lightweight computer-vision model runs locally or near the camera and checks for warning signals such as worker falls, missing PPE, restricted-area entry, smoke/fire, and blocked exits.

### Advanced Incident Analysis

When a possible incident is detected, SafetyLens captures a short event clip and sends only that clip to a multimodal AI model to verify the event, assign severity/confidence, explain evidence, retrieve the procedure, and recommend actions for human approval.

---

## Demo Scenario

For the hackathon demonstration, a prerecorded workplace video will eventually simulate a live camera feed from:

**Camera 04 — Loading Zone B**

Stage 1 already presents the resulting structured incident in the UI:

```json
{
  "incident_id": "INC-2026-0042",
  "incident_type": "worker_fall",
  "location": "Loading Zone B",
  "severity": "high",
  "confidence": 0.94,
  "evidence": "The worker experienced a sudden posture change and remained on the floor.",
  "recommended_actions": [
    "Alert the floor supervisor",
    "Request medical assistance",
    "Stop nearby machinery",
    "Preserve the incident footage",
    "Create an incident report"
  ]
}
```

---

## Technology Stack

### Frontend (Stage 1 — implemented)

- Next.js (App Router)
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- Lucide React
- Recharts (reports analytics)
- Local typed mock data

### Planned backend and AI stack

- Python / FastAPI
- OpenCV and lightweight detection
- Multimodal vision-language model
- Procedure retrieval / RAG
- PostgreSQL or equivalent
- Object storage for evidence

---

## Project Structure

```text
SafetyLens/
├── frontend/                 # Next.js operations console
│   ├── src/
│   │   ├── app/              # Routes and layouts
│   │   ├── components/       # Shell + domain UI components
│   │   ├── data/             # Fallback / mock data
│   │   ├── hooks/            # API resource hooks
│   │   ├── lib/api/          # Typed API client + mappers
│   │   └── types/            # UI view types
│   ├── .env.example
│   └── package.json
├── backend/                  # FastAPI Stage 2 service
│   ├── app/
│   │   ├── api/routes/       # REST endpoints
│   │   ├── core/             # Settings, enums, errors
│   │   ├── database/         # SQLAlchemy session
│   │   ├── models/           # ORM models
│   │   ├── schemas/          # Pydantic contracts
│   │   ├── services/         # Query services
│   │   └── seed/             # Idempotent demo seed
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
└── README.md
```

---

## Getting Started

### Prerequisites

- Node.js 18 or later
- Python 3.11 or later
- npm
- Git

No API keys are required for Stage 2.

### 1. Clone the repository

```bash
git clone https://github.com/Yug-More/SafetyLens.git
cd SafetyLens
```

### 2. Start the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.seed.run
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs: http://localhost:8000/docs

### 3. Start the frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open http://localhost:3000

### Environment variables

Frontend (`.env.local`):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_DEMO_FALLBACK=true
```

Backend (`.env`):

```env
APP_NAME=SafetyLens API
ENVIRONMENT=development
API_HOST=127.0.0.1
API_PORT=8000
DATABASE_URL=sqlite:///./safetylens.db
FRONTEND_ORIGINS=http://localhost:3000
DEMO_MODE=true
UPLOAD_DIRECTORY=./data/uploads
FRAME_DIRECTORY=./data/frames
MAX_VIDEO_SIZE_MB=100
MAX_VIDEO_DURATION_SECONDS=120
FRAME_SAMPLE_COUNT=10
```

### Video upload

1. Start backend and frontend.
2. Open **Live Monitor**.
3. Choose **Upload Demo Video**.
4. Select a short MP4/MOV/WebM clip (10–30 seconds recommended).
5. Confirm location (default Loading Zone B) and Camera 04.
6. Watch processing progress, then review playback and frame timeline.

Uploads require the live API. Offline demo fallback does **not** fake successful uploads.

### Fallback behavior

- API available → UI uses live API data
- API unavailable and `NEXT_PUBLIC_DEMO_FALLBACK=true` → centralized fallback data with a visible **Offline Demo Mode** banner (and a development console warning)
- API unavailable and fallback disabled → professional connection error with retry

### Useful commands

Frontend:

```bash
npm run dev
npm run build
npm run lint
npm run typecheck
```

Backend:

```bash
pytest
python -m app.seed.run
uvicorn app.main:app --reload
```

---

## Planned Future Stages

1. **Stage 4** — Multimodal AI verification, incident classification, confidence/evidence explanations
2. **Stage 5** — Approval execution, notifications, incident report generation
3. **Stage 6** — Multi-camera operations, auth/RBAC, production observability

---

## Why SafetyLens Is Different

Traditional camera systems answer:

> **What was recorded?**

Basic AI camera systems answer:

> **Did something unusual happen?**

SafetyLens answers:

> **What happened, how serious is it, which procedure applies, what should happen next, and were the required actions completed?**

---

## Responsible AI

SafetyLens is a decision-support system, not a replacement for emergency services or trained safety personnel.

The system is designed to:

- Display confidence and supporting evidence
- Keep consequential actions behind human approval
- Allow supervisors to modify or reject recommendations
- Record decisions for later review
- Minimize unnecessary video transmission

---

## Team

- **Yug More** — [GitHub: Yug-More](https://github.com/Yug-More)
- **Abhinav GS** — [GitHub: Abhinavgs1](https://github.com/Abhinavgs1)
- **Sean Aminov** — [GitHub: SeanAminov](https://github.com/SeanAminov)

---

## Disclaimer

This project is a hackathon prototype and should not be treated as a certified emergency-response or workplace-safety system. Critical safety decisions should always involve qualified personnel.

Stage 2 uses seeded API data with an optional offline demo fallback. It does not claim that real AI detection, video analysis, notifications, or emergency actions are operational.
