from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import IncidentStatus, Severity
from app.core.errors import AppError
from app.models.camera import Camera
from app.models.incident import Incident
from app.schemas.camera import CameraRead
from app.schemas.common import Meta
from app.schemas.incident import (
    EvidenceRead,
    IncidentDetail,
    IncidentRead,
    RecommendedActionRead,
)
from app.schemas.procedure import ProcedureRead
from app.services.procedures import procedure_to_read


def _incident_to_read(incident: Incident, camera_name: str | None = None) -> IncidentRead:
    payload = IncidentRead.model_validate(incident)
    if camera_name:
        payload.camera_name = camera_name
    elif incident.camera is not None:
        payload.camera_name = incident.camera.name
    return payload


def list_incidents(
    db: Session,
    *,
    severity: Severity | None = None,
    status: IncidentStatus | None = None,
    camera_id: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[IncidentRead], Meta]:
    query = select(Incident).options(selectinload(Incident.camera))
    if severity is not None:
        query = query.where(Incident.severity == severity.value)
    if status is not None:
        query = query.where(Incident.status == status.value)
    if camera_id:
        query = query.where(Incident.camera_id == camera_id)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                Incident.title.ilike(pattern),
                Incident.incident_code.ilike(pattern),
                Incident.location.ilike(pattern),
                Incident.incident_type.ilike(pattern),
            )
        )

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(Incident.detected_at.desc()).limit(limit).offset(offset)
    ).all()
    data = [_incident_to_read(row) for row in rows]
    return data, Meta(count=total, limit=limit, offset=offset)


def get_incident_detail(db: Session, identifier: str) -> IncidentDetail:
    query = (
        select(Incident)
        .options(
            selectinload(Incident.camera),
            selectinload(Incident.evidence_items),
            selectinload(Incident.actions),
            selectinload(Incident.matched_procedure),
        )
        .where(
            or_(
                Incident.id == identifier,
                Incident.incident_code == identifier,
            )
        )
    )
    incident = db.scalars(query).first()
    if incident is None:
        raise AppError("NOT_FOUND", "Incident not found", status_code=404)

    camera = incident.camera
    if camera is None:
        camera = db.get(Camera, incident.camera_id)
    if camera is None:
        raise AppError("NOT_FOUND", "Camera for incident not found", status_code=404)

    procedure = None
    if incident.matched_procedure is not None:
        procedure = procedure_to_read(incident.matched_procedure)

    return IncidentDetail(
        incident=_incident_to_read(incident, camera.name),
        camera=CameraRead.model_validate(camera),
        evidence=[EvidenceRead.model_validate(item) for item in incident.evidence_items],
        actions=[RecommendedActionRead.model_validate(item) for item in incident.actions],
        matched_procedure=procedure,
    )
