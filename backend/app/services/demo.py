from app.core.config import get_settings
from app.schemas.health import DemoInfo
from app.services.analysis import get_provider_info


def get_demo_info() -> DemoInfo:
    settings = get_settings()
    provider = get_provider_info(settings)
    return DemoInfo(
        demo_mode=settings.demo_mode,
        facility="Redwood Distribution Center",
        scenario="Camera 04 — Loading Zone B worker-fall review",
        description=(
            "Stage 4 demo environment with seeded operations data plus "
            f"multimodal analysis via {provider.label}."
        ),
        simulated_capabilities=[
            "Camera inventory and connection status",
            "Seeded incident detection records",
            "Video upload, metadata extraction, and frame sampling",
            f"Multimodal incident analysis ({provider.label})",
            "Human review of AI analysis before critical actions",
            "Procedure matching for demo scenarios",
            "Recommended actions awaiting human review",
            "System health and activity timeline",
        ],
        limitations=[
            "Live camera monitoring remains simulated unless Sean's detector is integrated.",
            f"Analysis provider in use: {provider.label}.",
            "Pose/detector scores are never treated as calibrated fall probability.",
            "Notifications and emergency alerts are not sent.",
            "Approval execution, SOP retrieval from analysis, and report generation arrive in later stages.",
            "No authentication / RBAC.",
        ],
    )
