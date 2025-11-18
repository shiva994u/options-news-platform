# backend/tools/article_analyzer.py
from __future__ import annotations

from typing import Literal, Dict, Any, Optional
import os
import json

import httpx
from bs4 import BeautifulSoup
from openai import OpenAI

Impact = Literal["Bullish", "Bearish", "Neutral"]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


# ---------- OpenAI client ----------

def get_openai_client() -> OpenAI:
    """
    Lazily create an OpenAI client using OPENAI_API_KEY.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
    return OpenAI(api_key=api_key)


# ---------- HTTP + HTML extraction ----------

async def fetch_article_html(url: str) -> str:
    async with httpx.AsyncClient(timeout=25, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        return resp.text


def extract_main_text(html: str) -> str:
    """
    Extract article body text from Yahoo Finance–style pages.

    We try, in order:
      1. div[data-test="caas-body"]        (common Yahoo Finance articles)
      2. div[data-test="article-body"]     (alternate Yahoo structure)
      3. div.bodyItems-wrapper             (some press release layouts)
      4. <article>                         (generic articles)
      5. All <p> tags as a last resort
    """
    soup = BeautifulSoup(html, "html.parser")

    body = (
        soup.select_one('div[data-test="caas-body"]')
        or soup.select_one('div[data-test="article-body"]')
        or soup.find("div", class_="bodyItems-wrapper")
        or soup.find("article")
    )

    if not body:
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        return "\n".join(paragraphs)

    paragraphs = [p.get_text(" ", strip=True) for p in body.find_all("p")]
    return "\n".join(paragraphs)


# ---------- Prompt builder ----------

def _build_llm_prompt(text: str, ticker: Optional[str]) -> str:
    """
    Build the user prompt for JSON impact analysis.
    """
    max_len = 8000  # trim long articles to avoid token blowup
    trimmed = text[:max_len]

    t = ticker or "the company"

    return (
        f"You are a professional equity analyst. Read the following news article "
        f"about {t} and assess the SHORT-TERM impact on the stock price.\n\n"
        "Return ONLY a JSON object, no extra text. Use this exact schema:\n\n"
        "{\n"
        '  \"overall\": \"Bullish\" | \"Bearish\" | \"Neutral\",\n'
        '  \"score\": number,            // positive for bullish, negative for bearish\n'
        '  \"rows\": [\n'
        "    {\n"
        '      \"factor\": string,       // short label like \"Float increase\", \"Earnings surprise\"\n'
        '      \"impact\": \"Bullish\" | \"Bearish\" | \"Neutral\",\n'
        '      \"reason\": string        // 1–2 sentences explaining why\n'
        "    },\n"
        "    ...\n"
        "  ]\n"
        "}\n\n"
        "Guidelines:\n"
        "- Focus on short-term impact (next few days), NOT long-term valuation.\n"
        "- Use multiple rows when there are multiple factors (offering, earnings, guidance, legal, etc.).\n"
        "- If impact is mixed or small, use overall = \"Neutral\".\n\n"
        "ARTICLE TEXT:\n"
        f"{trimmed}\n"
    )


# ---------- LLM classifier ----------

def classify_article_llm(text: str, ticker: Optional[str] = None) -> Dict[str, Any]:
    """
    Call OpenAI to classify article impact and return structured JSON.

    Returns:
      {
        "overall": "Bullish" | "Bearish" | "Neutral",
        "score": int,
        "rows": [{ "factor": str, "impact": str, "reason": str }]
      }

    If the article has no readable text, or the model returns invalid JSON,
    we return a simple Neutral structure.
    """
    # No content → trivial neutral
    if not text.strip():
        return {
            "overall": "Neutral",
            "score": 0,
            "rows": [
                {
                    "factor": "Content",
                    "impact": "Neutral",
                    "reason": "No readable article content could be extracted.",
                }
            ],
        }

    prompt = _build_llm_prompt(text, ticker)

    completion = get_openai_client().chat.completions.create(
        model="gpt-4.1-mini-2025-04-14",  # free / cheap model, ideal for this use case
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You are a precise financial news analyst that ONLY returns valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    raw_content = completion.choices[0].message.content or ""

    # Parse JSON content
    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError:
        return {
            "overall": "Neutral",
            "score": 0,
            "rows": [
                {
                    "factor": "Parsing",
                    "impact": "Neutral",
                    "reason": "The model response was not valid JSON.",
                }
            ],
        }

    # Basic normalization
    overall = data.get("overall", "Neutral")
    if overall not in ("Bullish", "Bearish", "Neutral"):
        overall = "Neutral"

    raw_score = data.get("score", 0)
    score: int
    if isinstance(raw_score, (int, float)):
        score = int(raw_score)
    else:
        score = 0

    rows = data.get("rows") or []

    cleaned_rows = []
    for r in rows:
        factor = str(r.get("factor", "Impact")).strip()
        impact = r.get("impact", "Neutral")
        if impact not in ("Bullish", "Bearish", "Neutral"):
            impact = "Neutral"
        reason = str(r.get("reason", "")).strip() or "No explanation provided."
        cleaned_rows.append(
            {"factor": factor, "impact": impact, "reason": reason}
        )

    if not cleaned_rows:
        cleaned_rows.append(
            {
                "factor": "Tone",
                "impact": overall,
                "reason": "No specific factors were extracted; classification is based on overall tone.",
            }
        )

    return {
        "overall": overall,
        "score": score,
        "rows": cleaned_rows,
    }
