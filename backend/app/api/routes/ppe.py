from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError
from app.database.session import get_db
from app.models.ppe_policy import CameraPpePolicy
from app.schemas.common import APIModel, CollectionResponse, ItemResponse, Meta

router = APIRouter(tags=["ppe"])


class CameraPpePolicyRead(APIModel):
    id: str
    camera_id: str
    camera_name: str | None = None
    zone_label: str
    required_ppe: list[str] = Field(default_factory=list)
    procedure_code: str
    is_active: bool


@router.get(
    "/api/ppe-policies",
    response_model=CollectionResponse[CameraPpePolicyRead],
)
def list_ppe_policies(
    db: Session = Depends(get_db),
) -> CollectionResponse[CameraPpePolicyRead]:
    rows = db.scalars(
        select(CameraPpePolicy)
        .options(selectinload(CameraPpePolicy.camera))
        .where(CameraPpePolicy.is_active.is_(True))
        .order_by(CameraPpePolicy.zone_label.asc())
    ).all()
    data = [
        CameraPpePolicyRead(
            id=row.id,
            camera_id=row.camera_id,
            camera_name=row.camera.name if row.camera else None,
            zone_label=row.zone_label,
            required_ppe=row.required_ppe,
            procedure_code=row.procedure_code,
            is_active=row.is_active,
        )
        for row in rows
    ]
    return CollectionResponse(data=data, meta=Meta(count=len(data), limit=50, offset=0))


@router.get(
    "/api/cameras/{camera_id}/ppe-policy",
    response_model=ItemResponse[CameraPpePolicyRead],
)
def get_camera_ppe_policy(
    camera_id: str,
    db: Session = Depends(get_db),
) -> ItemResponse[CameraPpePolicyRead]:
    row = db.scalars(
        select(CameraPpePolicy)
        .options(selectinload(CameraPpePolicy.camera))
        .where(CameraPpePolicy.camera_id == camera_id, CameraPpePolicy.is_active.is_(True))
    ).first()
    if row is None:
        raise AppError(
            "PPE_POLICY_NOT_FOUND",
            "No active PPE policy is configured for this camera.",
            status_code=404,
        )
    return ItemResponse(
        data=CameraPpePolicyRead(
            id=row.id,
            camera_id=row.camera_id,
            camera_name=row.camera.name if row.camera else None,
            zone_label=row.zone_label,
            required_ppe=row.required_ppe,
            procedure_code=row.procedure_code,
            is_active=row.is_active,
        )
    )
