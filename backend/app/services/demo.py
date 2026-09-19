from app.core.config import get_settings
from app.schemas.health import DemoInfo
from app.services.analysis import get_provider_info


def get_demo_info() -> DemoInfo:
    settings = get_settings()
    provider = get_provider_info(settings)
    planner = (
        "Demo Planner (simulated)"
        if settings.is_demo_planner
        else f"{settings.planner_provider} (real provider)"
    )
    return DemoInfo(
        demo_mode=settings.demo_mode,
        facility="Redwood Distribution Center",
        scenario="Camera 04 — Loading Zone B worker-fall review",
        description=(
            "Stage 7 integrated demo: uploaded-video fallback and optional detector "
            f"handoff, {provider.label}, lexical SOP retrieval, grounded plans, "
            f"human approval, simulated execution, audit timeline, and PDF reports "
            f"({planner})."
        ),
        simulated_capabilities=[
            "Camera inventory and connection status",
            "Video upload, frame sampling, and multimodal analysis",
            "Detector event ingestion with event_id deduplication",
            "Company procedure upload and verified citations",
            "Grounded response plans with human approval",
            "Simulated action execution (no real notifications)",
            "Append-only audit timeline and PDF incident reports",
            "Safe demo reset of seeded/runtime demo state",
        ],
        limitations=[
            "Detector pose_quality is landmark reliability — never fall probability.",
            "All executed actions are SIMULATED; no emergency services are contacted.",
            f"Analysis provider: {provider.label}. Planner: {planner}.",
            "Audit immutability is application-level on SQLite, not a compliance ledger.",
            "Authentication / RBAC remain prototype limitations.",
            "Sample SOP text is demonstration content, not legal advice.",
            "Webcam/RTSP live cameras are optional prototypes; known-video replay is the reliable demo path.",
        ],
    )
