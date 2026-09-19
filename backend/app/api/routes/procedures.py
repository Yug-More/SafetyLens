from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.common import CollectionResponse, ItemResponse, Meta
from app.schemas.procedure import (
    GenerateResponsePlanRequest,
    ProcedureChunkRead,
    ProcedureRead,
    ProcedureRetrievalRead,
    ProcedureUploadResponse,
    ResponsePlanRead,
    RetrieveProceduresRequest,
)
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


@router.post(
    "/api/procedures/upload",
    response_model=ItemResponse[ProcedureUploadResponse],
    status_code=201,
)
async def upload_procedure(
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    procedure_code: str = Form(...),
    title: str = Form(...),
    category: str = Form(default="General"),
    version: str = Form(default="1.0"),
    source_name: str | None = Form(default=None),
    effective_date: date | None = Form(default=None),
    is_sample: bool = Form(default=False),
) -> ItemResponse[ProcedureUploadResponse]:
    data = await procedure_service.upload_procedure(
        db,
        upload=file,
        procedure_code=procedure_code,
        title=title,
        category=category,
        version=version,
        source_name=source_name,
        effective_date=effective_date,
        is_sample=is_sample,
    )
    return ItemResponse(data=data)


@router.get(
    "/api/procedures/{procedure_identifier}",
    response_model=ItemResponse[ProcedureRead],
)
def get_procedure(
    procedure_identifier: str,
    db: Session = Depends(get_db),
) -> ItemResponse[ProcedureRead]:
    return ItemResponse(data=procedure_service.get_procedure(db, procedure_identifier))


@router.get(
    "/api/procedures/{procedure_identifier}/chunks",
    response_model=CollectionResponse[ProcedureChunkRead],
)
def list_procedure_chunks(
    procedure_identifier: str,
    db: Session = Depends(get_db),
) -> CollectionResponse[ProcedureChunkRead]:
    chunks = procedure_service.list_procedure_chunks(db, procedure_identifier)
    return CollectionResponse(
        data=chunks,
        meta=Meta(count=len(chunks), limit=len(chunks) or 1, offset=0),
    )
