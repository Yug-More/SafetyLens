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
            "Stage 5 demo with seeded operations data, multimodal analysis via "
            f"{provider.label}, lexical procedure retrieval, and {planner}."
        ),
        simulated_capabilities=[
            "Camera inventory and connection status",
            "Video upload, frame sampling, and multimodal analysis",
            "Company procedure upload (PDF/TXT/Markdown) and chunking",
            "Deterministic lexical retrieval with verified citations",
            "Grounded response plans (recommendations only)",
            "Human review of AI analysis before critical actions",
        ],
        limitations=[
            "Live camera monitoring remains simulated unless Sean's detector is integrated.",
            f"Analysis provider: {provider.label}. Planner: {planner}.",
            "Response plans are recommendations only — Stage 5 does not execute actions.",
            "Sample SOP text is demonstration content, not legal advice.",
            "Approval execution, notifications, and PDF reports arrive in Stage 6.",
            "No authentication / RBAC.",
        ],
    )
