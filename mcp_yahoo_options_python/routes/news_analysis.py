from __future__ import annotations

from typing import List, Literal, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from tools.article_analyzer import (
    fetch_article_html,
    extract_main_text,
    classify_article_llm,
)

Impact = Literal["Bullish", "Bearish", "Neutral"]


class ArticleImpactRow(BaseModel):
    factor: str
    impact: Impact
    reason: str


class ArticleAnalysisRequest(BaseModel):
    url: str
    ticker: Optional[str] = None


class ArticleAnalysisResponse(BaseModel):
    url: str
    ticker: Optional[str]
    overall: Impact
    score: int
    rows: List[ArticleImpactRow]
    summary: Optional[str] = None


router = APIRouter(prefix="/news", tags=["news"])


@router.post("/analyze-article", response_model=ArticleAnalysisResponse)
async def analyze_article(req: ArticleAnalysisRequest) -> ArticleAnalysisResponse:
    try:
        html = await fetch_article_html(req.url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch article: {e}")

    text = extract_main_text(html)
    if not text.strip():
        raise HTTPException(status_code=500, detail="Unable to extract article text")

    try:
        result = classify_article_llm(text, req.ticker)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM analysis failed: {e}")

    return ArticleAnalysisResponse(
        url=req.url,
        ticker=req.ticker,
        overall=result["overall"],
        score=int(result.get("score", 0)),
        rows=[ArticleImpactRow(**row) for row in result["rows"]],
        summary=None,
    )
