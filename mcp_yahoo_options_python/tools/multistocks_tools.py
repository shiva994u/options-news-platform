from __future__ import annotations

from typing import Literal, List, Dict

import math
import numbers
import yfinance as yf
from mcp.server.fastmcp import FastMCP

from tools.options_tools import build_option_chain_snapshot
from tools.news_tools import _scrape_yahoo_quote_section
from tools.ai_rating import get_ai_overall_rating

POSITIVE_NEWS_KEYWORDS = [
    "beat", "beats", "above expectations", "raises guidance",
    "upgrade", "upgraded", "initiated with buy", "outperform",
    "acquisition", "approved", "approval", "positive",
]

NEGATIVE_NEWS_KEYWORDS = [
    "miss", "misses", "below expectations", "lowers guidance",
    "downgrade", "downgraded", "sell rating",
    "lawsuit", "sec", "investigation", "recall", "warning",
    "negative", "disappointing",
]

def get_multi_symbol_snapshot(
    tickers: List[str],
    expiration: str | None,
    side: Literal["calls", "puts", "both"],
    limit: int,
    news_count: int,
    include_press_releases: bool,
) -> list[dict]:
    results: list[dict] = []

    for raw in tickers:
        symbol = (raw or "").upper().strip()
        if not symbol:
            continue

        snapshot: dict = {
            "ticker": symbol,
            "options": None,
            "news": [],
            "pressReleases": [],
            "error": None,
        }

        # options
        options_error = None
        try:
            snapshot["options"] = build_option_chain_snapshot(
                ticker=symbol,
                expiration=expiration,
                side=side,
                limit=limit,
            )
        except Exception as e:
            options_error = str(e)

        # news
        try:
            snapshot["news"] = _scrape_yahoo_quote_section(
                symbol, "news", news_count
            )
        except Exception as e:
            if snapshot["error"] is None:
                snapshot["error"] = f"News error: {e}"

        # press releases
        if include_press_releases:
            try:
                snapshot["pressReleases"] = _scrape_yahoo_quote_section(
                    symbol, "press-releases", news_count
                )
            except Exception as e:
                if snapshot["error"] is None:
                    snapshot["error"] = f"Press releases error: {e}"

        if options_error and snapshot["error"] is None:
            snapshot["error"] = options_error

        # ⭐ compute rating and attach
        snapshot["rating"] = _compute_rating_for_symbol(snapshot)
        
        try:
            ai_rating = get_ai_overall_rating(snapshot)
        except Exception as e:
            # don’t break everything if AI fails
            ai_rating = {
                "label": "Neutral",
                "numeric": 0.0,
                "timeframe": "1–3 days",
                "summary": "AI rating unavailable.",
                "factors": [],
                "source": f"error: {e}",
            }

        snapshot["aiRating"] = ai_rating
        results.append(snapshot)
    return results

def _safe_ratio(num: float | None, den: float | None) -> float | None:
    if num is None or den is None or den == 0:
        return None
    return num / den

def _score_news(news_items: list[dict]) -> int:
    score = 0
    for item in news_items:
        title = (item.get("title") or "").lower()
        for kw in POSITIVE_NEWS_KEYWORDS:
            if kw in title:
                score += 1
        for kw in NEGATIVE_NEWS_KEYWORDS:
            if kw in title:
                score -= 1
    return score

def _compute_rating_for_symbol(snapshot: dict) -> dict:
    """
    Compute rating scores based on:
    - volume vs avg_volume_3m
    - prev_close vs open vs current price
    - options call/put volume & intensity
    - news headlines
    Returns a rating dict; safe to attach as snapshot["rating"].
    """
    options = snapshot.get("options") or {}
    news = snapshot.get("news") or []

    current_vol = options.get("volume")
    avg_vol_3m = options.get("avg_volume_3m")
    prev_close = options.get("prev_close")
    open_price = options.get("open_price")
    current_price = options.get("underlying_price")

    # --- volume ratio ---
    volume_ratio = (
        _safe_ratio(current_vol, avg_vol_3m) if current_vol and avg_vol_3m else None
    )

    # Volume score
    if volume_ratio is None:
        volume_score = 0
    elif volume_ratio >= 3.0:
        volume_score = 2
    elif volume_ratio >= 1.5:
        volume_score = 1
    elif volume_ratio >= 0.7:
        volume_score = 0
    elif volume_ratio >= 0.4:
        volume_score = -1
    else:
        volume_score = -2

    # --- price action ---
    gap_percent = None
    intraday_change_percent = None

    if prev_close and open_price and prev_close > 0:
        gap_percent = (open_price - prev_close) / prev_close * 100.0

    if open_price and current_price and open_price > 0:
        intraday_change_percent = (current_price - open_price) / open_price * 100.0

    price_score = 0
    if gap_percent is not None:
        if gap_percent >= 3:
            price_score += 1
        elif gap_percent <= -3:
            price_score -= 1

    if intraday_change_percent is not None:
        if intraday_change_percent >= 2:
            price_score += 1
        elif intraday_change_percent <= -2:
            price_score -= 1

    price_score = max(-2, min(2, price_score))

    # --- options flow ---
    calls = options.get("calls") or []
    puts = options.get("puts") or []

    call_volume_total = sum((c.get("volume") or 0) for c in calls)
    put_volume_total = sum((p.get("volume") or 0) for p in puts)

    call_oi_total = sum((c.get("openInterest") or 0) for c in calls)
    put_oi_total = sum((p.get("openInterest") or 0) for p in puts)

    put_call_vol_ratio = (
        put_volume_total / call_volume_total if call_volume_total > 0 else None
    )
    put_call_oi_ratio = (
        put_oi_total / call_oi_total if call_oi_total > 0 else None
    )

    options_volume_total = call_volume_total + put_volume_total
    options_to_stock_vol_ratio = (
        options_volume_total / current_vol if current_vol and current_vol > 0 else None
    )

    options_score = 0
    if put_call_vol_ratio is not None:
        if put_call_vol_ratio < 0.7:
            options_score += 1
        elif put_call_vol_ratio > 1.3:
            options_score -= 1

    if options_to_stock_vol_ratio is not None:
        if options_to_stock_vol_ratio >= 0.5:
            options_score += 1
        # else: 0 (normal)

    options_score = max(-2, min(2, options_score))

    # --- news score ---
    raw_news_score = _score_news(news)
    if raw_news_score >= 3:
        news_score = 2
    elif raw_news_score >= 1:
        news_score = 1
    elif raw_news_score == 0:
        news_score = 0
    elif raw_news_score <= -3:
        news_score = -2
    else:
        news_score = -1

    # --- total ---
    total_score = volume_score + price_score + options_score + news_score

    if total_score >= 6:
        label = "Strong Buy"
    elif total_score >= 3:
        label = "Buy"
    elif total_score >= -2:
        label = "Neutral"
    elif total_score >= -5:
        label = "Sell"
    else:
        label = "Strong Sell"

    return {
        "label": label,
        "total_score": total_score,
        "volume_score": volume_score,
        "price_score": price_score,
        "options_score": options_score,
        "news_score": news_score,
        "volume_ratio": volume_ratio,
        "put_call_vol_ratio": put_call_vol_ratio,
        "put_call_oi_ratio": put_call_oi_ratio,
        "options_to_stock_vol_ratio": options_to_stock_vol_ratio,
        "gap_percent": gap_percent,
        "intraday_change_percent": intraday_change_percent,
        "raw_news_score": raw_news_score,
    }

def register_multi_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def get_multi_symbol_snapshot_tool(
        tickers: List[str],
        expiration: str | None = None,
        side: Literal["calls", "puts", "both"] = "both",
        limit: int = 20,
        news_count: int = 3,
        include_press_releases: bool = True,
    ) -> List[Dict]:
        return get_multi_symbol_snapshot(
            tickers=tickers,
            expiration=expiration,
            side=side,
            limit=limit,
            news_count=news_count,
            include_press_releases=include_press_releases,
        )
