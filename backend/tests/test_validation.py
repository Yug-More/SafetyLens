import pytest
from pydantic import ValidationError

from app.schemas.incident import EvidenceRead, IncidentCreate
from app.core.enums import IncidentStatus, ReviewStatus, Severity
from app.seed.seed_data import seed_database
from app.models.camera import Camera
from app.models.incident import Incident
from sqlalchemy import func, select


def test_confidence_validation_rejects_out_of_range():
    with pytest.raises(ValidationError):
        IncidentCreate(
            incident_code="INC-X",
            title="Bad Confidence",
            incident_type="worker_fall",
            location="Loading Zone B",
            camera_id="cam-04",
            severity=Severity.HIGH,
            confidence=1.5,
            evidence_summary="Invalid confidence",
            status=IncidentStatus.DETECTED,
            review_status=ReviewStatus.PENDING,
        )


def test_confidence_validation_accepts_bounds():
    model = IncidentCreate(
        incident_code="INC-Y",
        title="Valid Confidence",
        incident_type="worker_fall",
        location="Loading Zone B",
        camera_id="cam-04",
        severity=Severity.HIGH,
        confidence=0.94,
        evidence_summary="Valid confidence",
        status=IncidentStatus.DETECTED,
        review_status=ReviewStatus.PENDING,
    )
    assert model.confidence == 0.94


def test_timestamp_seconds_cannot_be_negative():
    with pytest.raises(ValidationError):
        EvidenceRead(
            id="ev-bad",
            incident_id="inc-1",
            evidence_type="posture_change",
            description="Bad timestamp",
            timestamp_seconds=-1,
            media_url=None,
            created_at="2026-09-19T00:00:00Z",
        )


def test_seed_idempotency(db_session):
    first = seed_database(db_session)
    second = seed_database(db_session)

    camera_count = db_session.scalar(select(func.count()).select_from(Camera))
    incident_count = db_session.scalar(select(func.count()).select_from(Incident))

    assert first["cameras"] == second["cameras"] == camera_count == 12
    assert first["incidents"] == second["incidents"] == incident_count == 4
