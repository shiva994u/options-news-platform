from __future__ import annotations

from typing import Literal

import math
import numbers
import yfinance as yf
from mcp.server.fastmcp import FastMCP


# ---------- PURE HELPERS (no MCP stuff) ----------

def build_option_chain_snapshot(
    ticker: str,
    expiration: str | None = None,
    side: Literal["calls", "puts", "both"] = "both",
    limit: int = 20,
) -> dict:
    symbol = ticker.upper()
    t = yf.Ticker(symbol)

    expirations = list(t.options)

    # No expirations at all → return empty options but still include stock info
    if not expirations:
        raw_underlying = _fast_info_get(t, "lastPrice")
        raw_prev_close = _fast_info_get(t, "previousClose")
        raw_open = _fast_info_get(t, "open")
        raw_volume = _fast_info_get(t, "lastVolume")
        raw_avg10 = _fast_info_get(t, "tenDayAverageVolume")
        raw_avg3m = _fast_info_get(t, "threeMonthAverageVolume")

        underlying_price = _clean_number(raw_underlying)
        prev_close = _clean_number(raw_prev_close)
        open_price = _clean_number(raw_open)
        current_volume = _clean_number(raw_volume)
        avg_volume_10d = _clean_number(raw_avg10)
        avg_volume_3m = _clean_number(raw_avg3m)

        earnings_date_iso = None
        try:
            edf = t.get_earnings_dates(limit=1)
            if edf is not None and not edf.empty:
                idx0 = edf.index[0]
                try:
                    earnings_date_iso = idx0.isoformat()
                except Exception:
                    earnings_date_iso = str(idx0)
        except Exception:
            earnings_date_iso = None

        return {
            "ticker": symbol,
            "expiration": None,
            "underlying_price": underlying_price,
            "prev_close": prev_close,
            "open_price": open_price,
            "volume": current_volume,
            "avg_volume_10d": avg_volume_10d,
            "avg_volume_3m": avg_volume_3m,
            "earnings_date": earnings_date_iso,
            "calls": [],
            "puts": [],
            "note": "No option expirations available; returned stock snapshot only.",
        }

    # Choose expiration (existing logic, with fallback to first)
    if expiration is None or expiration not in expirations:
        chosen_exp = expirations[0]
    else:
        chosen_exp = expiration

    chain = t.option_chain(chosen_exp)
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
        trimmed = df[cols].sort_values("volume", ascending=False).head(limit)
        records = trimmed.to_dict(orient="records")

        cleaned: list[dict] = []
        for rec in records:
            for key, val in rec.items():
                rec[key] = _clean_number(val)
            strike = rec.get("strike")
            if strike is None or strike <= 0:
                continue
            cleaned.append(rec)
        return cleaned

    # ---- Stock-level info ----
    raw_underlying = _fast_info_get(t, "lastPrice")
    raw_prev_close = _fast_info_get(t, "previousClose")
    raw_open = _fast_info_get(t, "open")
    raw_volume = _fast_info_get(t, "lastVolume")
    raw_avg10 = _fast_info_get(t, "tenDayAverageVolume")
    raw_avg3m = _fast_info_get(t, "threeMonthAverageVolume")

    underlying_price = _clean_number(raw_underlying)
    prev_close = _clean_number(raw_prev_close)
    open_price = _clean_number(raw_open)
    current_volume = _clean_number(raw_volume)
    avg_volume_10d = _clean_number(raw_avg10)
    avg_volume_3m = _clean_number(raw_avg3m)

    earnings_date_iso = None
    try:
        edf = t.get_earnings_dates(limit=1)
        if edf is not None and not edf.empty:
            idx0 = edf.index[0]
            try:
                earnings_date_iso = idx0.isoformat()
            except Exception:
                earnings_date_iso = str(idx0)
    except Exception:
        earnings_date_iso = None

    result: dict = {
        "ticker": symbol,
        "expiration": chosen_exp,
        "underlying_price": underlying_price,
        "prev_close": prev_close,
        "open_price": open_price,
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
    if isinstance(value, bool):
        return value

    if isinstance(value, numbers.Real):
        try:
            f = float(value)
        except (TypeError, ValueError):
            return None
        if math.isfinite(f):
            return f
        return None

    return value


def _fast_info_get(t: yf.Ticker, key: str):
    """Safely pull a field from fast_info."""
    try:
        if hasattr(t, "fast_info") and t.fast_info is not None:
            return t.fast_info.get(key, None)
    except Exception:
        return None
    return None


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
