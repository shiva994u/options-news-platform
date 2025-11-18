# backend/tools/article_analyzer.py
from __future__ import annotations

from typing import Literal, Dict, Any, Optional
import os
import json

import httpx
from bs4 import BeautifulSoup

Impact = Literal["Bullish", "Bearish", "Neutral"]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def get_groq_api_key() -> str:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY environment variable is not set.")
    return key


async def fetch_article_html(url: str) -> str:
    async with httpx.AsyncClient(timeout=25, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        return resp.text


def extract_main_text(html: str) -> str:
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


def _build_llm_prompt(text: str, ticker: Optional[str]) -> str:
    max_len = 8000
    trimmed = text[:max_len]
    t = ticker or "the company"

    return (
        f"You are a professional equity analyst. Read the following news article "
        f"about {t} and assess the SHORT-TERM impact on the stock price.\n\n"
        "Return ONLY a JSON object, no extra text. Use this exact schema:\n\n"
        "{\n"
        '  \"overall\": \"Bullish\" | \"Bearish\" | \"Neutral\",\n'
        '  \"score\": number,\n'
        '  \"rows\": [\n'
        "    {\n"
        '      \"factor\": string,\n'
        '      \"impact\": \"Bullish\" | \"Bearish\" | \"Neutral\",\n'
        '      \"reason\": string\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Guidelines:\n"
        "- Focus on short-term impact (next few days).\n"
        "- Use multiple rows when there are multiple factors.\n"
        "- If impact is mixed or small, use overall = \"Neutral\".\n\n"
        "ARTICLE TEXT:\n"
        f"{trimmed}\n"
    )


def classify_article_llm(text: str, ticker: Optional[str] = None) -> Dict[str, Any]:
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

    api_key = get_groq_api_key()

    resp = httpx.post(
        GROQ_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "llama-3.1-8b-instant",  # or any Groq-supported model
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": "You are a precise financial news analyst that ONLY returns valid JSON."
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        },
        timeout=60.0,
    )
    resp.raise_for_status()

    raw = resp.json()
    content = raw["choices"][0]["message"]["content"]

    try:
        data = json.loads(content)
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

    overall = data.get("overall", "Neutral")
    if overall not in ("Bullish", "Bearish", "Neutral"):
        overall = "Neutral"

    raw_score = data.get("score", 0)
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
                "reason": "No specific factors were extracted; overall tone only.",
            }
        )

    return {
        "overall": overall,
        "score": score,
        "rows": cleaned_rows,
    }
