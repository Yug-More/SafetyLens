from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import (
    ActionPriority,
    ActionStatus,
    CameraStatus,
    IncidentStatus,
    ReviewStatus,
    ServiceStatus,
    Severity,
)
from app.database.base import utc_now
from app.models.activity import ActivityEvent
from app.models.action import RecommendedAction
from app.models.camera import Camera
from app.models.evidence import Evidence
from app.models.incident import Incident
from app.models.procedure import SafetyProcedure
from app.models.system_service import SystemService

FACILITY_NAME = "Redwood Distribution Center"
SOURCE_NAME = "Redwood Distribution Center Safety Manual"

CAMERA_SEED = [
    ("cam-01", "Camera 01", "Main Entrance"),
    ("cam-02", "Camera 02", "Receiving Dock A"),
    ("cam-03", "Camera 03", "Packaging Floor"),
    ("cam-04", "Camera 04", "Loading Zone B"),
    ("cam-05", "Camera 05", "Quality Inspection"),
    ("cam-06", "Camera 06", "Break Room Corridor"),
    ("cam-07", "Camera 07", "Assembly Line 2"),
    ("cam-08", "Camera 08", "Forklift Lane East"),
    ("cam-09", "Camera 09", "Storage Zone C"),
    ("cam-10", "Camera 10", "Shipping Staging"),
    ("cam-11", "Camera 11", "Mezzanine Walkway"),
    ("cam-12", "Camera 12", "North Corridor"),
]

PROCEDURE_SEED = [
    {
        "id": "proc-fall",
        "procedure_code": "SOP-FALL-4.2",
        "title": "Worker Fall Response",
        "category": "Emergency Response",
        "version": "4.2",
        "content": (
            "1. Notify the floor supervisor immediately.\n"
            "2. Request medical assistance.\n"
            "3. Do not move the worker unless immediate danger exists.\n"
            "4. Stop nearby machinery.\n"
            "5. Preserve the relevant camera footage.\n"
            "6. Record the incident and all actions taken."
        ),
    },
    {
        "id": "proc-fire",
        "procedure_code": "SOP-FIRE-2.1",
        "title": "Fire and Smoke Response",
        "category": "Emergency Response",
        "version": "2.1",
        "content": (
            "1. Activate the nearest fire alarm.\n"
            "2. Evacuate personnel using designated routes.\n"
            "3. Contact emergency services.\n"
            "4. Account for all staff at muster points.\n"
            "5. Preserve camera evidence after evacuation."
        ),
    },
    {
        "id": "proc-ppe",
        "procedure_code": "SOP-PPE-3.4",
        "title": "PPE Compliance Procedure",
        "category": "Compliance",
        "version": "3.4",
        "content": (
            "1. Identify the non-compliant worker and zone.\n"
            "2. Issue an immediate PPE reminder.\n"
            "3. Pause work if risk remains elevated.\n"
            "4. Document the compliance event.\n"
            "5. Schedule refresher training if recurring."
        ),
    },
    {
        "id": "proc-restricted",
        "procedure_code": "SOP-ACCESS-5.1",
        "title": "Restricted Area Access Procedure",
        "category": "Access Control",
        "version": "5.1",
        "content": (
            "1. Confirm the restricted-zone boundary breach.\n"
            "2. Notify security and the area supervisor.\n"
            "3. Escort unauthorized personnel from the zone.\n"
            "4. Inspect for safety or inventory impact.\n"
            "5. Log the access event and corrective actions."
        ),
    },
]

SERVICE_SEED = [
    ("svc-cameras", "Camera Network", "12 of 12 connected"),
    ("svc-edge", "Edge Detector", "Simulated detector ready"),
    ("svc-ai", "AI Verification", "Demo mode"),
    ("svc-procedures", "Procedure Database", "Synchronized"),
    ("svc-notifications", "Notification Service", "Demo mode"),
]


def _get_or_create_camera(db: Session, camera_id: str, name: str, location: str) -> Camera:
    existing = db.get(Camera, camera_id)
    if existing:
        existing.name = name
        existing.location = location
        existing.status = CameraStatus.ONLINE.value
        existing.stream_status = "connected"
        existing.last_seen_at = utc_now()
        return existing

    camera = Camera(
        id=camera_id,
        name=name,
        location=location,
        status=CameraStatus.ONLINE.value,
        stream_status="connected",
        last_seen_at=utc_now(),
    )
    db.add(camera)
    return camera


def _get_or_create_procedure(db: Session, data: dict) -> SafetyProcedure:
    existing = db.scalars(
        select(SafetyProcedure).where(SafetyProcedure.procedure_code == data["procedure_code"])
    ).first()
    if existing:
        existing.title = data["title"]
        existing.category = data["category"]
        existing.version = data["version"]
        existing.content = data["content"]
        existing.source_name = SOURCE_NAME
        existing.is_active = True
        return existing

    procedure = SafetyProcedure(
        id=data["id"],
        procedure_code=data["procedure_code"],
        title=data["title"],
        category=data["category"],
        version=data["version"],
        content=data["content"],
        source_name=SOURCE_NAME,
        is_active=True,
    )
    db.add(procedure)
    return procedure


def _upsert_incident(
    db: Session,
    *,
    incident_id: str,
    incident_code: str,
    title: str,
    incident_type: str,
    location: str,
    camera_id: str,
    severity: Severity,
    confidence: float,
    evidence_summary: str,
    status: IncidentStatus,
    review_status: ReviewStatus,
    matched_procedure_id: str | None,
    detected_at: datetime,
) -> Incident:
    existing = db.scalars(
        select(Incident).where(Incident.incident_code == incident_code)
    ).first()
    if existing:
        existing.title = title
        existing.incident_type = incident_type
        existing.location = location
        existing.camera_id = camera_id
        existing.severity = severity.value
        existing.confidence = confidence
        existing.evidence_summary = evidence_summary
        existing.status = status.value
        existing.review_status = review_status.value
        existing.matched_procedure_id = matched_procedure_id
        existing.detected_at = detected_at
        return existing

    incident = Incident(
        id=incident_id,
        incident_code=incident_code,
        title=title,
        incident_type=incident_type,
        location=location,
        camera_id=camera_id,
        severity=severity.value,
        confidence=confidence,
        evidence_summary=evidence_summary,
        status=status.value,
        review_status=review_status.value,
        matched_procedure_id=matched_procedure_id,
        detected_at=detected_at,
    )
    db.add(incident)
    return incident


def _replace_children_for_primary(db: Session, incident: Incident) -> None:
    for item in list(incident.evidence_items):
        db.delete(item)
    for item in list(incident.actions):
        db.delete(item)
    db.flush()

    evidence_rows = [
        Evidence(
            id="ev-posture",
            incident_id=incident.id,
            evidence_type="posture_change",
            description="A sudden transition from standing to floor level was observed.",
            timestamp_seconds=8.2,
            media_url=None,
        ),
        Evidence(
            id="ev-inactivity",
            incident_id=incident.id,
            evidence_type="inactivity",
            description="The worker remained on the floor after the posture change.",
            timestamp_seconds=12.0,
            media_url=None,
        ),
    ]
    actions = [
        RecommendedAction(
            id="action-alert",
            incident_id=incident.id,
            title="Alert the floor supervisor",
            description="Notify the on-duty floor supervisor of a possible worker fall.",
            priority=ActionPriority.CRITICAL.value,
            status=ActionStatus.PENDING.value,
            requires_approval=True,
        ),
        RecommendedAction(
            id="action-medical",
            incident_id=incident.id,
            title="Request medical assistance",
            description="Request medical response for the affected worker.",
            priority=ActionPriority.CRITICAL.value,
            status=ActionStatus.PENDING.value,
            requires_approval=True,
        ),
        RecommendedAction(
            id="action-machinery",
            incident_id=incident.id,
            title="Stop nearby machinery",
            description="Halt equipment near Loading Zone B to protect responders.",
            priority=ActionPriority.HIGH.value,
            status=ActionStatus.PENDING.value,
            requires_approval=True,
        ),
        RecommendedAction(
            id="action-footage",
            incident_id=incident.id,
            title="Preserve incident footage",
            description="Retain the Camera 04 clip surrounding the detected event.",
            priority=ActionPriority.HIGH.value,
            status=ActionStatus.PENDING.value,
            requires_approval=True,
        ),
        RecommendedAction(
            id="action-report",
            incident_id=incident.id,
            title="Create an incident report",
            description="Prepare an auditable incident report after review.",
            priority=ActionPriority.STANDARD.value,
            status=ActionStatus.PENDING.value,
            requires_approval=True,
        ),
    ]
    db.add_all(evidence_rows)
    db.add_all(actions)


def _seed_activity(db: Session, primary_incident_id: str, now: datetime) -> None:
    desired = [
        (
            "act-1",
            "detection",
            "Worker-fall event detected",
            "Edge monitoring flagged a possible worker fall on Camera 04.",
            "warning",
            now - timedelta(seconds=14),
            primary_incident_id,
        ),
        (
            "act-2",
            "evidence",
            "Evidence clip preserved",
            "A short evidence clip was preserved for supervisor review.",
            "success",
            now - timedelta(seconds=12),
            primary_incident_id,
        ),
        (
            "act-3",
            "procedure",
            "Safety procedure matched",
            "Worker Fall Response — Section 4.2 was matched to the incident.",
            "success",
            now - timedelta(seconds=10),
            primary_incident_id,
        ),
        (
            "act-4",
            "review",
            "Supervisor review requested",
            "Human approval is required before recommended actions execute.",
            "pending",
            now - timedelta(seconds=8),
            primary_incident_id,
        ),
        (
            "act-5",
            "resolution",
            "Previous helmet incident resolved",
            "The earlier PPE compliance incident was marked resolved.",
            "success",
            now - timedelta(minutes=38),
            None,
        ),
    ]

    for event_id, event_type, title, description, status, occurred_at, incident_id in desired:
        existing = db.get(ActivityEvent, event_id)
        if existing:
            existing.event_type = event_type
            existing.title = title
            existing.description = description
            existing.status = status
            existing.occurred_at = occurred_at
            existing.incident_id = incident_id
            continue
        db.add(
            ActivityEvent(
                id=event_id,
                event_type=event_type,
                title=title,
                description=description,
                status=status,
                occurred_at=occurred_at,
                incident_id=incident_id,
            )
        )


def _seed_services(db: Session, now: datetime) -> None:
    for service_id, name, message in SERVICE_SEED:
        existing = db.scalars(select(SystemService).where(SystemService.name == name)).first()
        if existing:
            existing.status = ServiceStatus.OPERATIONAL.value
            existing.message = message
            existing.last_checked_at = now
            continue
        db.add(
            SystemService(
                id=service_id,
                name=name,
                status=ServiceStatus.OPERATIONAL.value,
                message=message,
                last_checked_at=now,
            )
        )


def seed_database(db: Session) -> dict[str, int]:
    now = datetime.now(timezone.utc)

    for camera_id, name, location in CAMERA_SEED:
        _get_or_create_camera(db, camera_id, name, location)
    db.flush()

    procedures = {
        item["procedure_code"]: _get_or_create_procedure(db, item) for item in PROCEDURE_SEED
    }
    db.flush()

    primary = _upsert_incident(
        db,
        incident_id="inc-2026-0042",
        incident_code="INC-2026-0042",
        title="Possible Worker Fall",
        incident_type="worker_fall",
        location="Loading Zone B",
        camera_id="cam-04",
        severity=Severity.HIGH,
        confidence=0.94,
        evidence_summary=(
            "The worker experienced a sudden posture change and remained on the floor."
        ),
        status=IncidentStatus.AWAITING_REVIEW,
        review_status=ReviewStatus.PENDING,
        matched_procedure_id=procedures["SOP-FALL-4.2"].id,
        detected_at=now - timedelta(seconds=14),
    )
    db.flush()
    _replace_children_for_primary(db, primary)

    _upsert_incident(
        db,
        incident_id="inc-2026-0041",
        incident_code="INC-2026-0041",
        title="Missing Safety Helmet",
        incident_type="ppe_violation",
        location="Assembly Line 2",
        camera_id="cam-07",
        severity=Severity.MEDIUM,
        confidence=0.91,
        evidence_summary=(
            "A worker entered the assembly area without a detectable safety helmet."
        ),
        status=IncidentStatus.RESOLVED,
        review_status=ReviewStatus.NOT_REQUIRED,
        matched_procedure_id=procedures["SOP-PPE-3.4"].id,
        detected_at=now - timedelta(minutes=38),
    )
    _upsert_incident(
        db,
        incident_id="inc-2026-0040",
        incident_code="INC-2026-0040",
        title="Restricted Area Entry",
        incident_type="restricted_area_entry",
        location="Storage Zone C",
        camera_id="cam-09",
        severity=Severity.MEDIUM,
        confidence=0.89,
        evidence_summary=(
            "An unauthorized person crossed into a marked restricted storage zone."
        ),
        status=IncidentStatus.RESOLVED,
        review_status=ReviewStatus.NOT_REQUIRED,
        matched_procedure_id=procedures["SOP-ACCESS-5.1"].id,
        detected_at=now - timedelta(hours=2),
    )
    _upsert_incident(
        db,
        incident_id="inc-2026-0039",
        incident_code="INC-2026-0039",
        title="Obstructed Emergency Exit",
        incident_type="blocked_exit",
        location="North Corridor",
        camera_id="cam-12",
        severity=Severity.LOW,
        confidence=0.87,
        evidence_summary=(
            "Pallet staging partially blocked the marked emergency exit pathway."
        ),
        status=IncidentStatus.CLOSED,
        review_status=ReviewStatus.NOT_REQUIRED,
        matched_procedure_id=None,
        detected_at=now - timedelta(days=1),
    )

    _seed_activity(db, primary.id, now)
    _seed_services(db, now)
    db.commit()

    return {
        "cameras": len(db.scalars(select(Camera)).all()),
        "incidents": len(db.scalars(select(Incident)).all()),
        "procedures": len(db.scalars(select(SafetyProcedure)).all()),
        "services": len(db.scalars(select(SystemService)).all()),
        "activity": len(db.scalars(select(ActivityEvent)).all()),
    }
