# backend/tools/ai_rating.py
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple
import os
import json
import math

import httpx

RatingLabel = Literal["Strong Buy", "Buy", "Neutral", "Sell", "Avoid"]
Impact = Literal["Bullish", "Bearish", "Neutral"]

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


# ---------- Helpers ----------

def get_groq_api_key() -> str:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY environment variable is not set.")
    return key


def safe_div(num: Optional[float], denom: Optional[float]) -> Optional[float]:
    if num is None or denom in (None, 0):
        return None
    try:
        return num / denom
    except ZeroDivisionError:
        return None


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


# ---------- Metrics extraction from snapshot ----------

def build_metrics_payload(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adapt this to your real snapshot structure if needed.
    This assumes something like:
      snapshot = {
        "ticker": "LB",
        "underlying_price": 61.88,
        "prev_close": 70.50,
        "open": 70.50,
        "volume": 1_782_661,
        "avg_volume_3m": 280_000,
        "options_summary": {
            "call_volume": 12000,
            "put_volume": 8000,
            "total_call_oi": 50000,
            "total_put_oi": 30000,
        },
        "news_sentiment_score": 0,  # -2..+2 if you have it, else 0
      }
    """

    opts = snapshot.get("options_summary") or {}

    last = snapshot.get("underlying_price") or snapshot.get("last") or snapshot.get("close")
    prev_close = snapshot.get("prev_close")
    open_price = snapshot.get("open")

    volume = snapshot.get("volume")
    avg_vol_3m = snapshot.get("avg_volume_3m")

    call_vol = opts.get("call_volume")
    put_vol = opts.get("put_volume")

    volume_ratio = safe_div(volume, avg_vol_3m)
    pct_change = (
        safe_div((last - prev_close), prev_close) * 100 # type: ignore
        if last is not None and prev_close not in (None, 0)
        else None
    )
    gap_pct = (
        safe_div((open_price - prev_close), prev_close) * 100 # type: ignore
        if open_price is not None and prev_close not in (None, 0)
        else None
    )
    put_call_ratio = safe_div(put_vol, call_vol)

    return {
        "ticker": snapshot.get("ticker"),
        "underlying_price": last,
        "prev_close": prev_close,
        "open": open_price,
        "volume_today": volume,
        "avg_volume_3m": avg_vol_3m,
        "volume_ratio": volume_ratio,
        "pct_change": pct_change,
        "gap_pct": gap_pct,
        "call_volume": call_vol,
        "put_volume": put_vol,
        "put_call_ratio": put_call_ratio,
        # optional: if you have aggregated news sentiment, else 0
        "news_score_raw": snapshot.get("news_sentiment_score", 0),
    }


# ---------- Rule-based scoring (-2 .. +2) ----------

def score_volume(vol_ratio: Optional[float]) -> int:
    if vol_ratio is None:
        return 0
    if vol_ratio >= 4:
        return +2
    if vol_ratio >= 2:
        return +1
    if 0.7 <= vol_ratio <= 1.5:
        return 0
    if vol_ratio >= 0.4:
        return -1
    return -2


def score_price(pct_change: Optional[float], gap_pct: Optional[float]) -> int:
    """
    Very simple price action scoring:
      - Strong up day or gap up → bullish
      - Strong down day or gap down → bearish
    """
    if pct_change is None:
        return 0

    score = 0

    # Daily move
    if pct_change >= 5:
        score += 2
    elif pct_change >= 3:
        score += 1
    elif pct_change <= -5:
        score -= 2
    elif pct_change <= -3:
        score -= 1

    # Gap
    if gap_pct is not None:
        if gap_pct >= 3:
            score += 1
        elif gap_pct <= -3:
            score -= 1

    # Clamp to -2..+2
    return int(clamp(score, -2, 2))


def score_options(put_call_ratio: Optional[float]) -> int:
    """
    Options scoring based on put/call volume ratio.
    You can extend with relative vol vs average later.
    """
    if put_call_ratio is None:
        return 0

    # Very call-heavy
    if put_call_ratio <= 0.5:
        return +2
    if put_call_ratio <= 0.8:
        return +1
    if 0.8 < put_call_ratio < 1.2:
        return 0
    if put_call_ratio <= 1.5:
        return -1
    return -2


def score_news(raw_news_score: Any) -> int:
    """
    If you already compute a sentiment score elsewhere (-2..+2), just pass it through.
    For now we clamp whatever we see into -2..+2 range.
    """
    try:
        val = float(raw_news_score)
    except (TypeError, ValueError):
        return 0
    return int(clamp(val, -2, 2))


def impact_from_score(score: int) -> Impact:
    if score >= 1:
        return "Bullish"
    if score <= -1:
        return "Bearish"
    return "Neutral"


def map_overall_label(numeric: float) -> RatingLabel:
    if numeric >= 1.5:
        return "Strong Buy"
    if numeric >= 0.5:
        return "Buy"
    if numeric <= -1.5:
        return "Avoid"
    if numeric <= -0.5:
        return "Sell"
    return "Neutral"


# ---------- Build base (non-AI) rating ----------

def build_rule_based_rating(snapshot: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Returns (base_rating, metrics).
    base_rating has:
      {
        "label": ...,
        "numeric": float,
        "timeframe": "1–3 days",
        "summary": "",
        "factors": [
          {"name", "impact", "score", "reason"},
          ...
        ],
        "source": "rules"
      }
    """
    metrics = build_metrics_payload(snapshot)

    vol_score = score_volume(metrics.get("volume_ratio"))
    price_score = score_price(metrics.get("pct_change"), metrics.get("gap_pct"))
    options_score = score_options(metrics.get("put_call_ratio"))
    news_score = score_news(metrics.get("news_score_raw"))

    overall_numeric = (
        0.3 * vol_score +
        0.3 * price_score +
        0.25 * options_score +
        0.15 * news_score
    )
    overall_numeric = float(clamp(overall_numeric, -2.0, 2.0))
    label = map_overall_label(overall_numeric)

    factors: List[Dict[str, Any]] = []

    # Volume factor
    vr = metrics.get("volume_ratio")
    vol_reason = "Volume data not available."
    if vr is not None:
        vol_reason = f"Volume is {vr:.1f}× the 3-month average."
    factors.append(
        {
            "name": "Volume",
            "impact": impact_from_score(vol_score),
            "score": vol_score,
            "reason": vol_reason,
        }
    )

    # Price factor
    pct = metrics.get("pct_change")
    gap = metrics.get("gap_pct")
    if pct is None:
        price_reason = "Price change data not available."
    else:
        price_reason = f"Price moved {pct:.1f}% today."
        if gap is not None and abs(gap) >= 1.0:
            price_reason += f" Opened with a {gap:.1f}% gap."
    factors.append(
        {
            "name": "Price action",
            "impact": impact_from_score(price_score),
            "score": price_score,
            "reason": price_reason,
        }
    )

    # Options factor
    pcr = metrics.get("put_call_ratio")
    if pcr is None:
        opt_reason = "Options volume data not available."
    else:
        cp = metrics.get("call_volume")
        pp = metrics.get("put_volume")
        opt_reason = f"Put/Call volume ratio is {pcr:.2f}."
        if cp is not None and pp is not None:
            opt_reason += f" Calls: {cp}, Puts: {pp}."
    factors.append(
        {
            "name": "Options flow",
            "impact": impact_from_score(options_score),
            "score": options_score,
            "reason": opt_reason,
        }
    )

    # News factor
    if news_score == 0:
        news_reason = "News impact is neutral or not evaluated."
    elif news_score > 0:
        news_reason = "Recent news is short-term bullish."
    else:
        news_reason = "Recent news is short-term bearish."
    factors.append(
        {
            "name": "News",
            "impact": impact_from_score(news_score),
            "score": news_score,
            "reason": news_reason,
        }
    )

    base_rating: Dict[str, Any] = {
        "label": label,
        "numeric": overall_numeric,
        "timeframe": "1–3 days",
        "summary": "",
        "factors": factors,
        "source": "rules",
    }
    return base_rating, metrics


# ---------- Groq enrichment: better summary & reasons ----------

def enrich_rating_with_groq(
    base_rating: Dict[str, Any],
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Send metrics + base_rating to Groq and ask it to:
      - keep label & numeric as-is
      - rewrite a clearer summary (1–2 sentences)
      - improve factor 'reason' texts
    If anything fails, we just return the base_rating.
    """
    try:
        api_key = get_groq_api_key()
    except RuntimeError:
        # No key → just return the rule-based rating
        return base_rating

    prompt = (
        "You are a short-term equity trading analyst.\n"
        "You are given:\n"
        "  1) A metrics JSON for a stock.\n"
        "  2) A base rating JSON that already contains label, numeric score, and factor scores.\n\n"
        "Your job:\n"
        "- DO NOT change the 'label' or 'numeric' fields in base_rating.\n"
        "- DO NOT change the 'score' numbers in each factor.\n"
        "- You MAY slightly adjust each factor's 'impact' between Bullish/Bearish/Neutral "
        "  if it better matches the score and metrics, but keep it consistent.\n"
        "- Write a concise 1–2 sentence 'summary' explaining the overall setup "
        "  for the next 1–3 days (long-side focus).\n"
        "- Rewrite each factor's 'reason' to be clear, concrete, and rooted in the metrics.\n\n"
        "Return ONLY JSON with this exact schema:\n"
        "{\n"
        "  \"label\": string,          // same as base_rating.label\n"
        "  \"numeric\": number,        // same as base_rating.numeric\n"
        "  \"timeframe\": string,      // e.g. \"1–3 days\"\n"
        "  \"summary\": string,\n"
        "  \"factors\": [\n"
        "    { \"name\": string, \"impact\": \"Bullish\"|\"Bearish\"|\"Neutral\", \"score\": number, \"reason\": string }\n"
        "  ]\n"
        "}\n"
    )

    payload = {
        "metrics": metrics,
        "base_rating": base_rating,
    }

    json_input = json.dumps(payload, indent=2)

    with httpx.Client(timeout=60.0) as client:
        resp = client.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a precise, risk-aware trading assistant. "
                            "You MUST output valid JSON only."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt + "\n\nINPUT JSON:\n" + json_input,
                    },
                ],
                "temperature": 0.2,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"]
    try:
        enriched = json.loads(content)
    except json.JSONDecodeError:
        # If Groq returns non-JSON, just keep rule-based rating
        return base_rating

    # Sanity: enforce label & numeric from base_rating
    enriched["label"] = base_rating["label"]
    enriched["numeric"] = base_rating["numeric"]
    enriched.setdefault("timeframe", base_rating.get("timeframe", "1–3 days"))

    # Clean factors
    factors = enriched.get("factors") or base_rating["factors"]
    cleaned_factors: List[Dict[str, Any]] = []
    for f in factors:
        name = str(f.get("name", "Factor"))
        impact = f.get("impact", "Neutral")
        if impact not in ("Bullish", "Bearish", "Neutral"):
            impact = "Neutral"
        score = f.get("score", 0)
        if not isinstance(score, (int, float)):
            score = 0
        reason = str(f.get("reason", "") or "No explanation provided.")
        cleaned_factors.append(
            {"name": name, "impact": impact, "score": score, "reason": reason}
        )

    enriched["factors"] = cleaned_factors
    enriched["source"] = "groq+rules"
    return enriched


# ---------- Public entry ----------

def get_ai_overall_rating(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to be called from your endpoint.

    Usage in multi-snapshot builder:
        base = build_symbol_snapshot(...)
        ai = get_ai_overall_rating(base)
        base["aiRating"] = ai
    """
    base_rating, metrics = build_rule_based_rating(snapshot)
    try:
        return enrich_rating_with_groq(base_rating, metrics)
    except Exception as e:
        # Any Groq/network error → fall back to rule-based rating
        print(f"[ai_rating] Groq enrichment failed, using rules only: {e}")
        base_rating["source"] = "rules_error"
        base_rating.setdefault(
            "summary",
            "AI enrichment unavailable; using rule-based rating only.",
        )
        return base_rating
