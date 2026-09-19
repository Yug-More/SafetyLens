from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.common import CollectionResponse, ItemResponse
from app.schemas.procedure import ProcedureRead
from app.services import procedures as procedure_service

router = APIRouter(tags=["procedures"])


@router.get("/api/procedures", response_model=CollectionResponse[ProcedureRead])
def list_procedures(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None),
    category: str | None = Query(default=None),
    active: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> CollectionResponse[ProcedureRead]:
    data, meta = procedure_service.list_procedures(
        db,
        search=search,
        category=category,
        active=active,
        limit=limit,
        offset=offset,
    )
    return CollectionResponse(data=data, meta=meta)


@router.get(
    "/api/procedures/{procedure_identifier}",
    response_model=ItemResponse[ProcedureRead],
)
def get_procedure(
    procedure_identifier: str,
    db: Session = Depends(get_db),
) -> ItemResponse[ProcedureRead]:
    return ItemResponse(data=procedure_service.get_procedure(db, procedure_identifier))
