from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db import SessionLocal
from app.db_models import VideoRow
from app.research.models import ResearchReport
from app.research.service import research_story

router = APIRouter(prefix="/research", tags=["research"])


class ResearchStoryRequest(BaseModel):
    query: str | None = None
    claims: list[str] = Field(default_factory=list)
    video_id: UUID | None = None


@router.post("/story")
def research_story_route(request: ResearchStoryRequest) -> ResearchReport:
    query = request.query
    if request.video_id:
        with SessionLocal() as session:
            video = session.get(VideoRow, request.video_id)
        if video is None:
            raise HTTPException(status_code=404, detail="Video not found")
        query = video.title

    if not query:
        raise HTTPException(status_code=422, detail="Provide query or video_id")

    return research_story(query=query, claims=request.claims)
