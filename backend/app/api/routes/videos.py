from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import VideoStatus
from app.core.errors import AppError
from app.database.session import get_db
from app.schemas.common import CollectionResponse, ItemResponse, Meta
from app.schemas.video import (
    ProcessingJobRead,
    VideoAssetRead,
    VideoFrameRead,
    VideoUploadResponse,
)
from app.services import storage
from app.services import videos as video_service

router = APIRouter(tags=["videos"])


@router.post(
    "/api/videos/upload",
    response_model=ItemResponse[VideoUploadResponse],
    status_code=202,
)
async def upload_video(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    location: str = Form(...),
    camera_id: str | None = Form(default=None),
) -> ItemResponse[VideoUploadResponse]:
    response, video_id = await video_service.create_upload(
        db,
        upload=file,
        location=location,
        camera_id=camera_id or None,
    )
    job = video_service.get_job(db, response.job_code)
    background_tasks.add_task(video_service.process_video_job, video_id, job.id)
    return ItemResponse(data=response)


@router.get("/api/videos", response_model=CollectionResponse[VideoAssetRead])
def list_videos(
    db: Session = Depends(get_db),
    status: VideoStatus | None = None,
    camera_id: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> CollectionResponse[VideoAssetRead]:
    data, meta = video_service.list_videos(
        db,
        status=status,
        camera_id=camera_id,
        search=search,
        limit=limit,
        offset=offset,
    )
    return CollectionResponse(data=data, meta=meta)


@router.get("/api/videos/{video_identifier}", response_model=ItemResponse[VideoAssetRead])
def get_video(
    video_identifier: str,
    db: Session = Depends(get_db),
) -> ItemResponse[VideoAssetRead]:
    return ItemResponse(data=video_service.get_video(db, video_identifier))


@router.get(
    "/api/videos/{video_identifier}/frames",
    response_model=CollectionResponse[VideoFrameRead],
)
def get_video_frames(
    video_identifier: str,
    db: Session = Depends(get_db),
) -> CollectionResponse[VideoFrameRead]:
    frames = video_service.list_video_frames(db, video_identifier)
    return CollectionResponse(
        data=frames,
        meta=Meta(count=len(frames), limit=len(frames) or 1, offset=0),
    )


@router.get("/api/videos/{video_identifier}/content")
def get_video_content(
    video_identifier: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    """Stream uploaded video for local demo playback.

    Note: Stage 3 serves the full file via FileResponse. Explicit HTTP Range
    handling is not implemented; browsers can still play short demo videos.
    """
    settings = get_settings()
    video = video_service.get_video_entity(db, video_identifier)
    path = storage.resolve_upload_path(video.stored_filename, settings)
    if not path.exists():
        raise AppError("NOT_FOUND", "Video content is unavailable.", status_code=404)
    return FileResponse(
        path=path,
        media_type=video.mime_type,
        filename=video.original_filename,
        content_disposition_type="inline",
    )


@router.get(
    "/api/processing-jobs/{job_identifier}",
    response_model=ItemResponse[ProcessingJobRead],
)
def get_processing_job(
    job_identifier: str,
    db: Session = Depends(get_db),
) -> ItemResponse[ProcessingJobRead]:
    return ItemResponse(data=video_service.get_job(db, job_identifier))


@router.get("/api/frames/{frame_identifier}/content")
def get_frame_content(
    frame_identifier: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    settings = get_settings()
    frame = video_service.get_frame_entity(db, frame_identifier)
    path = storage.resolve_frame_path(frame.stored_filename, settings)
    if not path.exists():
        raise AppError("NOT_FOUND", "Frame content is unavailable.", status_code=404)
    return FileResponse(
        path=path,
        media_type="image/jpeg",
        filename=Path(frame.stored_filename).name,
        content_disposition_type="inline",
    )
