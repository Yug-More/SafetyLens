from __future__ import annotations

import json

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.database.session import get_db
from app.schemas.common import CollectionResponse, ItemResponse, Meta
from app.schemas.detector import (
    DetectorEventIngestRequest,
    DetectorEventPayload,
    DetectorEventRead,
    DemoResetRequest,
    DemoResetResponse,
)
from app.services import detector_ingestion as detector_service
from app.services import demo_reset as demo_reset_service

router = APIRouter(tags=["detector"])


@router.post(
    "/api/detector/events",
    response_model=ItemResponse[DetectorEventRead],
    status_code=202,
)
async def ingest_detector_event(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    event_json: str = Form(..., description="Detector event JSON (schema_version 1.0)"),
    clip: UploadFile | None = File(default=None),
    location: str = Form(default="Loading Zone B"),
    auto_analyze: bool = Form(default=True),
    incident_identifier: str | None = Form(default="INC-2026-0042"),
) -> ItemResponse[DetectorEventRead]:
    try:
        raw = json.loads(event_json)
    except json.JSONDecodeError as exc:
        raise AppError(
            "INVALID_EVENT_JSON",
            "event_json must be valid JSON matching the detector contract.",
            status_code=422,
        ) from exc
    try:
        event = DetectorEventPayload.model_validate(raw)
    except Exception as exc:
        raise AppError(
            "INVALID_DETECTOR_EVENT",
            str(exc),
            status_code=422,
        ) from exc

    request = DetectorEventIngestRequest(
        event=event,
        location=location,
        auto_analyze=auto_analyze,
        incident_identifier=incident_identifier,
    )
    data = await detector_service.ingest_detector_event(
        db,
        request,
        clip=clip,
        background_tasks=background_tasks,
    )
    return ItemResponse(data=data)


@router.get(
    "/api/detector/events",
    response_model=CollectionResponse[DetectorEventRead],
)
def list_detector_events(
    db: Session = Depends(get_db),
    limit: int = 20,
) -> CollectionResponse[DetectorEventRead]:
    data = detector_service.list_detector_events(db, limit=limit)
    return CollectionResponse(data=data, meta=Meta(count=len(data), limit=limit, offset=0))


@router.get(
    "/api/detector/events/{event_id}",
    response_model=ItemResponse[DetectorEventRead],
)
def get_detector_event(
    event_id: str,
    db: Session = Depends(get_db),
) -> ItemResponse[DetectorEventRead]:
    return ItemResponse(
        data=detector_service.advance_ingestion(
            db,
            event_id,
            auto_analyze=False,
        )
    )


@router.post(
    "/api/detector/events/{event_id}/retry",
    response_model=ItemResponse[DetectorEventRead],
)
def retry_detector_event(
    event_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ItemResponse[DetectorEventRead]:
    data = detector_service.retry_detector_event(
        db,
        event_id,
        background_tasks=background_tasks,
    )
    return ItemResponse(data=data)


@router.post(
    "/api/demo/reset",
    response_model=ItemResponse[DemoResetResponse],
)
def reset_demo(
    payload: DemoResetRequest,
    db: Session = Depends(get_db),
) -> ItemResponse[DemoResetResponse]:
    return ItemResponse(data=demo_reset_service.reset_demo_state(db, payload))
