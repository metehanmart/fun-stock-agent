from __future__ import annotations

import json as _json

import pandas as pd
import yfinance as yf

from models.schemas import AssetType


class MarketDataError(Exception):
    """Raised when market data cannot be retrieved or is incomplete."""


def _pct_change(current: float, past: float) -> float:
    """Return percentage change from *past* to *current*, rounded to 2 dp."""
    if past == 0:
        return 0.0
    return round((current - past) / past * 100, 2)


def fetch_market_data(ticker: str, asset_type: AssetType) -> dict:
    """
    Fetch market data for *ticker* using yfinance and return a normalised dict
    ready for the analyser.

    Raises
    ------
    MarketDataError
        If the ticker is unknown, the exchange returned no data, or key fields
        are missing from the response.
    """
    symbol = ticker.upper().strip()

    asset = yf.Ticker(symbol)

    # Try the full info dict first; fall back gracefully if the endpoint is
    # unavailable (e.g. rate-limited) — yfinance raises JSONDecodeError in that case.
    info: dict = {}
    try:
        info = asset.info or {}
    except (_json.JSONDecodeError, Exception):
        pass  # will fall back to fast_info below

    # Validate the ticker returned meaningful data.
    # If info is empty, treat it as unknown — fast_info won't give us a name.
    long_name: str = (
        info.get("longName")
        or info.get("shortName")
        or info.get("displayName")
        or ""
    )

    # Current price — prefer info fields, fall back to fast_info.last_price
    current_price: float | None = (
        info.get("currentPrice")
        or info.get("regularMarketPrice")
        or info.get("previousClose")
        or info.get("navPrice")
    )

    if current_price is None:
        # Attempt fast_info as a lightweight fallback
        try:
            fi = asset.fast_info
            current_price = fi.last_price or fi.regular_market_previous_close
            if not long_name:
                # fast_info has no name — use the symbol itself as a placeholder
                long_name = symbol
            currency_fi: str = getattr(fi, "currency", None) or "USD"
        except Exception as exc:
            raise MarketDataError(
                f"Current price unavailable for '{symbol}'. "
                "The market may be closed or the ticker may be unsupported."
            ) from exc
    else:
        currency_fi = None

    if current_price is None:
        raise MarketDataError(
            f"Current price unavailable for '{symbol}'. "
            "The market may be closed or the ticker may be unsupported."
        )
    current_price = float(current_price)

    if not long_name:
        raise MarketDataError(
            f"No data found for ticker '{symbol}'. "
            "Please check the symbol and asset type."
        )

    currency: str = info.get("currency") or currency_fi or "USD"

    # Historical closes — we need ~210 trading days to cover 200-day MA + 3-month change
    try:
        history: pd.DataFrame = asset.history(period="1y", auto_adjust=True)
    except Exception as exc:
        raise MarketDataError(f"Failed to fetch price history: {exc}") from exc

    if history.empty or len(history) < 10:
        raise MarketDataError(
            f"Insufficient price history for '{symbol}'."
        )

    closes: pd.Series = history["Close"].dropna()

    # --- Percentage changes ---
    def _close_n_days_ago(n: int) -> float | None:
        if len(closes) >= n:
            return float(closes.iloc[-n])
        return None

    close_5d = _close_n_days_ago(6)   # 5 trading days back
    close_1m = _close_n_days_ago(22)  # ~1 calendar month
    close_3m = _close_n_days_ago(66)  # ~3 calendar months

    change_5d = _pct_change(current_price, close_5d) if close_5d else 0.0
    change_1m = _pct_change(current_price, close_1m) if close_1m else 0.0
    change_3m = _pct_change(current_price, close_3m) if close_3m else 0.0

    # --- Moving averages ---
    ma_50: float | None = (
        round(float(closes.tail(50).mean()), 2) if len(closes) >= 50 else None
    )
    ma_200: float | None = (
        round(float(closes.tail(200).mean()), 2) if len(closes) >= 200 else None
    )

    return {
        "ticker": symbol,
        "asset_type": asset_type,
        "company_name": long_name,
        "currency": currency,
        "current_price": round(current_price, 4),
        "change_5d_pct": change_5d,
        "change_1m_pct": change_1m,
        "change_3m_pct": change_3m,
        "ma_50": ma_50,
        "ma_200": ma_200,
    }
