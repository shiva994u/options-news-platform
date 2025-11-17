from __future__ import annotations

from typing import Literal, List, Dict

import math
import numbers
import yfinance as yf
from mcp.server.fastmcp import FastMCP

from tools.options_tools import build_option_chain_snapshot
from tools.news_tools import _scrape_yahoo_quote_section

def get_multi_symbol_snapshot(
    tickers: List[str],
    expiration: str | None = None,
    side: Literal["calls", "puts", "both"] = "both",
    limit: int = 20,
    news_count: int = 3,
    include_press_releases: bool = True,
) -> List[Dict]:
    """Fetch multi-symbol snapshot with options, news, and press releases."""
    results: List[Dict] = []

    for raw in tickers:
        symbol = (raw or "").upper().strip()
        if not symbol:
            continue

        snapshot: Dict = {
            "ticker": symbol,
            "options": None,
            "news": [],
            "pressReleases": [],
            "error": None,          # overall error
        }

        options_error = None

        # ---- OPTIONS (non-fatal) ----
        try:
            # reuse the exact same logic as the single-symbol tool
            options_payload = build_option_chain_snapshot(
                ticker=symbol,
                expiration=expiration,
                side=side,
                limit=limit,
            )
            snapshot["options"] = options_payload
        except Exception as e:
            options_error = str(e)

        # ---- PRESS RELEASES (optional, always attempted) ----
        if include_press_releases:
            try:
                pr_items = _scrape_yahoo_quote_section(
                    symbol, "press-releases", news_count
                )
                snapshot["pressReleases"] = pr_items
            except Exception as e:
                if snapshot["error"] is None:
                    snapshot["error"] = f"Press releases error: {e}"

        # attach options_error if nothing else set
        if options_error and snapshot["error"] is None:
            snapshot["error"] = options_error

        results.append(snapshot)

    return results

def _clean_number(value):
    """
    Convert NaN/inf to None so JSON encoding doesn't crash.
    Leave booleans and non-numeric types unchanged.
    """
    # Don't touch booleans
    if isinstance(value, bool):
        return value

    # Handle numeric (int, float, numpy scalars, etc.)
    if isinstance(value, numbers.Real):
        try:
            f = float(value)
        except (TypeError, ValueError):
            return None
        if math.isfinite(f):
            return f
        return None  # NaN or +/-inf → None

    # Anything else (str, None, etc.) pass through
    return value

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
