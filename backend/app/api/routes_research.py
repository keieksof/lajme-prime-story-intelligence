from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.research.models import ResearchReport
from app.research.service import research_story

router = APIRouter(prefix="/research", tags=["research"])


class ResearchStoryRequest(BaseModel):
    query: str
    claims: list[str] = []


@router.post("/story")
def research_story_route(request: ResearchStoryRequest) -> ResearchReport:
    return research_story(query=request.query, claims=request.claims)
