from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, HttpUrl

from app.db import SessionLocal
from app.repositories.story_repository import StoryRepository
from app.services.story_graph import StoryGraphService, serialize_graph_result
from app.story_engine.analyzer import HeuristicStoryAnalyzer
from app.story_engine.llm_analyzer import LLMStoryAnalyzer
from app.story_engine.pipeline import StoryIntelligencePipeline

router = APIRouter(prefix="/stories", tags=["stories"])


class AnalyzeStoryRequest(BaseModel):
    title: str
    text: str
    source_url: HttpUrl | None = None


def _build_pipeline() -> StoryIntelligencePipeline:
    mode = os.getenv("STORY_ANALYZER", "heuristic").strip().lower()
    analyzer = LLMStoryAnalyzer() if mode == "llm" else HeuristicStoryAnalyzer()
    return StoryIntelligencePipeline(analyzer)


def _response_from_result(result: Any) -> dict[str, Any]:
    response = dict(result.analysis)
    if result.research is not None:
        response["research"] = result.research
    return response


@router.post("/analyze")
def analyze_story(request: AnalyzeStoryRequest) -> dict[str, Any]:
    result = _build_pipeline().process(
        title=request.title,
        text=request.text,
        source_url=str(request.source_url) if request.source_url else None,
    )
    return _response_from_result(result)


@router.post("/analyze-and-link")
def analyze_and_link_story(request: AnalyzeStoryRequest) -> dict[str, Any]:
    result = _build_pipeline().process(
        title=request.title,
        text=request.text,
        source_url=str(request.source_url) if request.source_url else None,
    )
    from app.models.domain import StoryAnalysis

    analysis = StoryAnalysis(**result.analysis)
    with SessionLocal() as session:
        graph_result = StoryGraphService(StoryRepository(session)).ingest(analysis)
        session.commit()

    response = _response_from_result(result)
    response["graph"] = serialize_graph_result(graph_result)
    return response
