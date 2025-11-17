# backend/api_server.py
from __future__ import annotations

from typing import List, Literal, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from fastapi.middleware.cors import CORSMiddleware

from tools.options_tools import build_option_chain_snapshot, list_option_expirations
from tools.news_tools import _scrape_yahoo_quote_section
from tools.multistocks_tools import get_multi_symbol_snapshot  # if you expose helper separately

app = FastAPI(title="Options News API")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://options-news-platform.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # or ["*"] for everything in dev
    allow_credentials=True,
    allow_methods=["*"],          # allow POST, GET, OPTIONS, etc.
    allow_headers=["*"],          # allow Content-Type, Authorization, etc.
)


# ---- Pydantic models for request bodies ----

class MultiSnapshotRequest(BaseModel):
    tickers: List[str]
    expiration: Optional[str] = None
    side: Literal["calls", "puts", "both"] = "both"
    limit: int = 20
    news_count: int = 3
    include_press_releases: bool = True


# ---- Health ----

@app.get("/health")
def health():
    return {"status": "ok"}


# ---- Single symbol options chain ----

@app.get("/options/chain/{ticker}")
def get_options_chain(
    ticker: str,
    expiration: Optional[str] = None,
    side: Literal["calls", "puts", "both"] = "both",
    limit: int = 20,
):
    snapshot = build_option_chain_snapshot(
        ticker=ticker,
        expiration=expiration,
        side=side,
        limit=limit,
    )
    return snapshot


@app.get("/options/expirations/{ticker}")
def get_expirations(ticker: str):
    return {"ticker": ticker.upper(), "expirations": list_option_expirations(ticker)}


# ---- News / press releases ----

@app.get("/news/{ticker}")
def get_news(ticker: str, count: int = 5):
    items = _scrape_yahoo_quote_section(ticker, "news", count)
    return {"ticker": ticker.upper(), "items": items}


@app.get("/press-releases/{ticker}")
def get_press_releases(ticker: str, count: int = 5):
    items = _scrape_yahoo_quote_section(ticker, "press-releases", count)
    return {"ticker": ticker.upper(), "items": items}


# ---- Multi-symbol snapshot (reuse your multi_tools logic) ----
# If your multi_tools exposes a helper function, call it here.
# For now, assume there is a function: build_multi_symbol_snapshot(...)

from tools.multistocks_tools import get_multi_symbol_snapshot  # you can extract this

@app.post("/options/multi-snapshot")
def multi_snapshot(body: MultiSnapshotRequest):
    result = get_multi_symbol_snapshot(
        tickers=body.tickers,
        expiration=body.expiration,
        side=body.side,
        limit=body.limit,
        news_count=body.news_count,
        include_press_releases=body.include_press_releases,
    )
    return result
