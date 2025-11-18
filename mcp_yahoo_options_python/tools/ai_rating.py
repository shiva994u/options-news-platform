from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
import json
import os

from openai import OpenAI

RatingLabel = Literal["Strong Buy", "Buy", "Neutral", "Sell", "Avoid"]
Impact = Literal["Bullish", "Bearish", "Neutral"]

def get_openai_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


def build_metrics_payload(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Take your existing snapshot dict and distill only what the LLM needs.
    Adjust field names to match your real snapshot structure.
    """
    rating = snapshot.get("rating", {}) or {}

    return {
        "ticker": snapshot.get("ticker"),
        "underlying_price": snapshot.get("underlying_price"),
        "volume_today": snapshot.get("volume"),
        "avg_volume_3m": snapshot.get("avg_volume_3m"),
        "volume_ratio": rating.get("volume_ratio"),          # e.g. 4.2
        "volume_score": rating.get("volume_score"),          # your -2..+2

        "price_change_pct": rating.get("price_change_pct"),  # today % change
        "price_score": rating.get("price_score"),            # -2..+2

        "put_call_ratio": rating.get("put_call_ratio"),
        "call_volume": rating.get("call_volume"),
        "put_volume": rating.get("put_volume"),
        "options_score": rating.get("options_score"),

        "news_score": rating.get("news_score"),              # -2..+2
        "news_highlights": rating.get("news_highlights"),    # short text if you have it
    }


def build_ai_prompt(metrics: Dict[str, Any]) -> str:
    """
    Ask the model to act like a short-term trading analyst.
    """
    return (
        "You are a short-term equity trading analyst. "
        "You will receive structured metrics for a stock and you must decide whether "
        "it is an interesting LONG trade setup for the next 1–3 trading days.\n\n"
        "Metrics JSON:\n"
        f"{json.dumps(metrics, indent=2)}\n\n"
        "Produce ONLY a JSON object with this schema:\n"
        "{\n"
        '  \"label\": \"Strong Buy\" | \"Buy\" | \"Neutral\" | \"Sell\" | \"Avoid\",\n'
        "  \"numeric\": number,      // overall score between -2 and +2\n"
        "  \"timeframe\": string,    // short text like \"1–3 days\"\n"
        "  \"summary\": string,      // 1–2 sentence overview\n"
        "  \"factors\": [\n"
        "    {\n"
        '      \"name\": string,     // e.g. \"Volume\", \"Price action\", \"Options flow\", \"News\"\n'
        '      \"impact\": \"Bullish\" | \"Bearish\" | \"Neutral\",\n'
        "      \"score\": number,    // -2..+2 for this factor\n"
        "      \"reason\": string    // 1 sentence explanation\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Guidelines:\n"
        "- Focus on the 1–3 day horizon, not long-term investing.\n"
        "- Be conservative: use \"Strong Buy\" only for very clean setups.\n"
        "- If signals conflict, choose \"Neutral\" and explain why.\n"
        "- Make sure the JSON is valid and follows the schema exactly.\n"
    )


def get_ai_overall_rating(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function: call OpenAI and return a structured AI rating object.
    """
    metrics = build_metrics_payload(snapshot)
    prompt = build_ai_prompt(metrics)

    client = get_openai_client()

    completion = client.chat.completions.create(
        # use one of your allowed models; update if needed
        model="gpt-4.1-mini-2025-04-14",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise, risk-aware trading analyst. "
                    "You ONLY return valid JSON following the requested schema."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    raw = completion.choices[0].message.content or "{}"
    data = json.loads(raw)

    # Basic normalization
    label = data.get("label", "Neutral")
    if label not in ["Strong Buy", "Buy", "Neutral", "Sell", "Avoid"]:
        label = "Neutral"

    numeric = data.get("numeric", 0.0)
    if not isinstance(numeric, (int, float)):
        numeric = 0.0

    summary = data.get("summary", "")
    timeframe = data.get("timeframe", "1–3 days")

    factors = data.get("factors") or []
    cleaned_factors: List[Dict[str, Any]] = []
    for f in factors:
        name = str(f.get("name", "Factor"))
        impact = f.get("impact", "Neutral")
        if impact not in ("Bullish", "Bearish", "Neutral"):
            impact = "Neutral"
        score = f.get("score", 0.0)
        if not isinstance(score, (int, float)):
            score = 0.0
        reason = str(f.get("reason", "") or "No explanation provided.")
        cleaned_factors.append(
            {"name": name, "impact": impact, "score": score, "reason": reason}
        )

    if not cleaned_factors:
        cleaned_factors.append(
            {
                "name": "Overall",
                "impact": "Neutral",
                "score": 0,
                "reason": "No specific factor-level explanation was provided.",
            }
        )

    return {
        "label": label,
        "numeric": float(numeric),
        "timeframe": timeframe,
        "summary": summary,
        "factors": cleaned_factors,
        "source": "openai",
    }
