from app.core.config import get_settings
from app.schemas.health import DemoInfo


def get_demo_info() -> DemoInfo:
    settings = get_settings()
    return DemoInfo(
        demo_mode=settings.demo_mode,
        facility="Redwood Distribution Center",
        scenario="Camera 04 — Loading Zone B worker-fall review",
        description=(
            "Stage 2 demo environment with seeded camera, incident, procedure, "
            "and activity data for policy-grounded human approval workflows."
        ),
        simulated_capabilities=[
            "Camera inventory and connection status",
            "Seeded incident detection records",
            "Procedure matching for demo scenarios",
            "Recommended actions awaiting human review",
            "System health and activity timeline",
        ],
        limitations=[
            "Live camera monitoring is simulated in Stage 2.",
            "AI verification is simulated in Stage 2.",
            "Notifications and emergency alerts are not sent.",
            "Approval execution and report generation are not implemented yet.",
            "Video processing and multimodal analysis arrive in Stage 3.",
        ],
    )
