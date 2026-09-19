from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.analysis import (
    AIProviderInfo,
    AnalysisReviewCreate,
    AnalyzeVideoResponse,
    IncidentAnalysisRead,
)
from app.schemas.common import CollectionResponse, ItemResponse
from app.services import analysis as analysis_service

router = APIRouter(tags=["analysis"])


@router.get("/api/ai/provider", response_model=ItemResponse[AIProviderInfo])
def get_ai_provider_info() -> ItemResponse[AIProviderInfo]:
    return ItemResponse(data=analysis_service.get_provider_info())


@router.post(
    "/api/videos/{video_identifier}/analyze",
    response_model=ItemResponse[AnalyzeVideoResponse],
    status_code=202,
)
def analyze_video(
    video_identifier: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ItemResponse[AnalyzeVideoResponse]:
    response = analysis_service.start_analysis(db, video_identifier)
    analysis = analysis_service.get_analysis(db, response.analysis_code)
    background_tasks.add_task(
        analysis_service.run_analysis_job,
        analysis.id,
        analysis.processing_job_id,
    )
    return ItemResponse(data=response)


@router.get(
    "/api/videos/{video_identifier}/analyses",
    response_model=CollectionResponse[IncidentAnalysisRead],
)
def list_video_analyses(
    video_identifier: str,
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> CollectionResponse[IncidentAnalysisRead]:
    data, meta = analysis_service.list_video_analyses(
        db,
        video_identifier,
        limit=limit,
        offset=offset,
    )
    return CollectionResponse(data=data, meta=meta)


@router.get(
    "/api/analyses/{analysis_identifier}",
    response_model=ItemResponse[IncidentAnalysisRead],
)
def get_analysis(
    analysis_identifier: str,
    db: Session = Depends(get_db),
) -> ItemResponse[IncidentAnalysisRead]:
    return ItemResponse(data=analysis_service.get_analysis(db, analysis_identifier))


@router.post(
    "/api/analyses/{analysis_identifier}/review",
    response_model=ItemResponse[IncidentAnalysisRead],
)
def submit_analysis_review(
    analysis_identifier: str,
    payload: AnalysisReviewCreate,
    db: Session = Depends(get_db),
) -> ItemResponse[IncidentAnalysisRead]:
    return ItemResponse(
        data=analysis_service.submit_review(db, analysis_identifier, payload)
    )
