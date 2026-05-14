from __future__ import annotations

from models.schemas import AnalysisResponse, AssetType


# ---------------------------------------------------------------------------
# Internal scoring helpers
# ---------------------------------------------------------------------------

def _score_momentum(change_5d: float, change_1m: float, change_3m: float) -> int:
    """
    Return a momentum score in the range [-3, +3].
    Each timeframe contributes +1 (positive) or -1 (negative).
    """
    score = 0
    score += 1 if change_5d > 0 else -1
    score += 1 if change_1m > 0 else -1
    score += 1 if change_3m > 0 else -1
    return score


def _trend_relative_to_ma(
    price: float,
    ma_50: float | None,
    ma_200: float | None,
) -> tuple[str, int]:
    """
    Derive a human-readable trend label and a secondary score based on the
    position of *price* relative to moving averages.

    Returns (label, score) where score is in [-2, +2].
    """
    above_50 = price > ma_50 if ma_50 is not None else None
    above_200 = price > ma_200 if ma_200 is not None else None
    golden_cross = (ma_50 > ma_200) if (ma_50 and ma_200) else None

    score = 0
    if above_50 is True:
        score += 1
    elif above_50 is False:
        score -= 1

    if above_200 is True:
        score += 1
    elif above_200 is False:
        score -= 1

    # Label derivation
    if above_50 is None and above_200 is None:
        label = "Insufficient data"
    elif above_50 is True and above_200 is True:
        label = "Strong uptrend" if golden_cross else "Uptrend"
    elif above_50 is False and above_200 is False:
        label = "Strong downtrend" if golden_cross is False else "Downtrend"
    elif above_50 is True and above_200 is False:
        label = "Recovery — below 200-day MA"
    else:
        label = "Weakening — below 50-day MA"

    return label, score


def _assess_risk(
    change_5d: float,
    change_1m: float,
    change_3m: float,
    asset_type: AssetType,
) -> str:
    """
    Assign a simple risk category based on recent volatility and asset class.
    """
    # Use the absolute swings as a rough proxy for volatility
    avg_abs_swing = (abs(change_5d) + abs(change_1m) + abs(change_3m)) / 3

    # Indexes and broad ETFs are inherently lower risk than single stocks
    base_low_threshold = 3.0
    base_high_threshold = 8.0
    if asset_type == AssetType.index:
        base_low_threshold, base_high_threshold = 2.0, 5.0
    elif asset_type == AssetType.etf:
        base_low_threshold, base_high_threshold = 2.5, 6.0

    if avg_abs_swing <= base_low_threshold:
        return "Low"
    elif avg_abs_swing <= base_high_threshold:
        return "Medium"
    else:
        return "High"


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def analyze(data: dict) -> AnalysisResponse:
    """
    Apply a rule-based analysis to the raw *data* dict returned by
    ``market_data.fetch_market_data`` and produce an :class:`AnalysisResponse`.

    The logic is intentionally transparent and simple — this is a demo.
    """
    price: float = data["current_price"]
    change_5d: float = data["change_5d_pct"]
    change_1m: float = data["change_1m_pct"]
    change_3m: float = data["change_3m_pct"]
    ma_50: float | None = data["ma_50"]
    ma_200: float | None = data["ma_200"]
    asset_type: AssetType = data["asset_type"]

    # --- Scoring ---
    momentum_score = _score_momentum(change_5d, change_1m, change_3m)
    trend_label, ma_score = _trend_relative_to_ma(price, ma_50, ma_200)
    total_score = momentum_score + ma_score  # range: [-5, +5]

    risk_level = _assess_risk(change_5d, change_1m, change_3m, asset_type)

    # --- Advice mapping ---
    #   total_score >= 3  → Buy
    #   total_score in [1, 2] → Hold
    #   total_score == 0  → Watch
    #   total_score <= -1 → Avoid
    if total_score >= 3:
        advice = "Buy"
        advice_reason = (
            "Positive momentum across multiple timeframes and price is trading "
            "above key moving averages, suggesting a sustained uptrend."
        )
    elif total_score >= 1:
        advice = "Hold"
        advice_reason = (
            "Mixed signals — some positive momentum but not yet a clear "
            "breakout. Existing positions may be maintained; new entries "
            "should await confirmation."
        )
    elif total_score == 0:
        advice = "Watch"
        advice_reason = (
            "Neutral momentum with no clear directional conviction. "
            "Monitor for a decisive move before taking action."
        )
    else:
        advice = "Avoid"
        advice_reason = (
            "Negative momentum across multiple timeframes or price is "
            "trading below key moving averages, indicating downward pressure."
        )

    # Elevate caution for high-risk assets
    if risk_level == "High" and advice == "Buy":
        advice = "Watch"
        advice_reason = (
            "Potential uptrend detected, but elevated volatility warrants "
            "caution. Monitor closely before committing capital."
        )

    return AnalysisResponse(
        ticker=data["ticker"],
        asset_type=asset_type,
        company_name=data["company_name"],
        currency=data["currency"],
        current_price=price,
        change_5d_pct=change_5d,
        change_1m_pct=change_1m,
        change_3m_pct=change_3m,
        ma_50=ma_50,
        ma_200=ma_200,
        trend_status=trend_label,
        risk_level=risk_level,
        advice=advice,
        advice_reason=advice_reason,
    )
