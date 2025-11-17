from __future__ import annotations

from typing import Literal

import math
import numbers
import yfinance as yf
from mcp.server.fastmcp import FastMCP


# ---------- PURE HELPERS (no MCP stuff) ----------

def _fast_info_get(t: yf.Ticker, key: str):
    """Safely pull a field from fast_info."""
    try:
        if hasattr(t, "fast_info") and t.fast_info is not None:
            return t.fast_info.get(key, None)
    except Exception:
        return None
    return None

def build_option_chain_snapshot(
    ticker: str,
    expiration: str | None = None,
    side: Literal["calls", "puts", "both"] = "both",
    limit: int = 20,
) -> dict:
    """
    Core logic to fetch and format an options chain snapshot for one symbol.
    This is safe to call from anywhere (single tool, multi-symbol tool, etc.).
    """
    symbol = ticker.upper()
    t = yf.Ticker(symbol)

    expirations = list(t.options)

    # Case 4 – No expirations at all
    if not expirations:
        return {
            "ticker": symbol,
            "expiration": None,
            "underlying_price": t.fast_info.get("lastPrice", None)
            if hasattr(t, "fast_info")
            else None,
            "calls": [],
            "puts": [],
            "note": "No option expirations available; returned empty chain."
        }

    # Normalize expiration choice
    if expiration is None:
        # Case 3 – no expiration provided → use first available
        chosen_exp = expirations[0]
    else:
        # Case 2 – expiration not valid → use first available
        if expiration not in expirations:
            chosen_exp = expirations[0]
        else:
            chosen_exp = expiration

    chain = t.option_chain(chosen_exp)  # returns .calls and .puts DataFrames
    calls_df = chain.calls
    puts_df = chain.puts

    def simplify(df):
        if df is None or df.empty:
            return []
        wanted = [
            "contractSymbol",
            "strike",
            "lastPrice",
            "bid",
            "ask",
            "volume",
            "openInterest",
            "impliedVolatility",
            "inTheMoney",
        ]
        cols = [c for c in wanted if c in df.columns]
        if not cols:
            return []

        # sort by volume and take the top N rows
        trimmed = df[cols].sort_values("volume", ascending=False).head(limit)

        records = trimmed.to_dict(orient="records")

        cleaned: list[dict] = []
        for rec in records:
            # sanitize numeric fields
            for key, val in rec.items():
                rec[key] = _clean_number(val)

            # drop broken rows where strike is missing or <= 0
            strike = rec.get("strike")
            if strike is None or strike <= 0:
                continue

            cleaned.append(rec)

        return cleaned

    # ---- Underlying price ----
    raw_underlying = _fast_info_get(t, "lastPrice")
    underlying_price = _clean_number(raw_underlying)
    
    # ---- Volume & average volumes ----
    raw_volume = _fast_info_get(t, "lastVolume")  # current day volume (so far)
    raw_avg10 = _fast_info_get(t, "tenDayAverageVolume")  # 10-day avg
    raw_avg3m = _fast_info_get(t, "threeMonthAverageVolume")  # 3-month avg

    current_volume = _clean_number(raw_volume)
    avg_volume_10d = _clean_number(raw_avg10)
    avg_volume_3m = _clean_number(raw_avg3m)
    
    # ---- Earnings date (next upcoming, if available) ----
    earnings_date_iso = None
    try:
        # yfinance get_earnings_dates(limit=1) gives a DataFrame indexed by date
        edf = t.get_earnings_dates(limit=1)
        if edf is not None and not edf.empty:
            # index[0] is a Timestamp
            next_ed = edf.index[0]
            try:
                earnings_date_iso = next_ed.isoformat()
            except Exception:
                earnings_date_iso = str(next_ed)
    except Exception:
        earnings_date_iso = None

    result: dict = {
        "ticker": symbol,
        "expiration": chosen_exp,
        "underlying_price": underlying_price,
        "volume": current_volume,
        "avg_volume_10d": avg_volume_10d,
        "avg_volume_3m": avg_volume_3m,
        "earnings_date": earnings_date_iso,
    }

    if side in ("calls", "both"):
        result["calls"] = simplify(calls_df)
    if side in ("puts", "both"):
        result["puts"] = simplify(puts_df)

    return result


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


def list_option_expirations(ticker: str) -> list[str]:
    """
    List available option expiration dates for a symbol (YYYY-MM-DD).
    """
    symbol = ticker.upper()
    t = yf.Ticker(symbol)
    return list(t.options)


# ---------- MCP REGISTRATION LAYER ----------

def register_options_tools(mcp: FastMCP) -> None:
    """
    Register all options-related tools on the given MCP server.
    """

    @mcp.tool()
    def get_option_chain(
        ticker: str,
        expiration: str | None = None,
        side: Literal["calls", "puts", "both"] = "both",
        limit: int = 20,
    ) -> dict:
        """
        Get an options chain for a stock from Yahoo Finance.
        """
        return build_option_chain_snapshot(
            ticker=ticker,
            expiration=expiration,
            side=side,
            limit=limit,
        )

    @mcp.tool()
    def get_option_expirations(ticker: str) -> list[str]:
        """
        List available option expiration dates for a symbol (YYYY-MM-DD).
        """
        return list_option_expirations(ticker)
