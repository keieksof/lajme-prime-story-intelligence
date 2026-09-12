from fastapi import APIRouter
from pydantic import BaseModel, HttpUrl

from app.story_engine.analyzer import HeuristicStoryAnalyzer
from app.story_engine.pipeline import StoryIntelligencePipeline

router = APIRouter(prefix="/stories", tags=["stories"])
pipeline = StoryIntelligencePipeline(HeuristicStoryAnalyzer())


class AnalyzeStoryRequest(BaseModel):
    title: str
    text: str
    source_url: HttpUrl | None = None


@router.post("/analyze")
def analyze_story(request: AnalyzeStoryRequest) -> dict:
    result = pipeline.process(
        title=request.title,
        text=request.text,
        source_url=str(request.source_url) if request.source_url else None,
    )
    return result.analysis
