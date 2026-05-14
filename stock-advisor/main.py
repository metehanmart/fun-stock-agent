from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import AnalysisRequest, AnalysisResponse, AssetType, ErrorResponse
from services.market_data import MarketDataError, fetch_market_data
from services.analyzer import analyze

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Stock Advisor Demo",
    description=(
        "A simple demo application that fetches market data and returns a "
        "rule-based analysis for stocks, ETFs/funds, and indexes.\n\n"
        "**Disclaimer:** This application is for educational purposes only. "
        "It does not constitute financial advice and must not be used to execute trades."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def root() -> dict:
    """Health-check endpoint."""
    return {"status": "ok", "message": "Stock Advisor Demo API is running."}


@app.get(
    "/asset-types",
    tags=["Reference"],
    summary="List supported asset types",
)
def get_asset_types() -> dict:
    """Return the supported asset type values."""
    return {
        "asset_types": [
            {"value": AssetType.stock, "label": "Stock"},
            {"value": AssetType.etf,   "label": "ETF / Fund"},
            {"value": AssetType.index, "label": "Index"},
        ]
    }


@app.post(
    "/analyze",
    response_model=AnalysisResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid ticker or missing data"},
        502: {"model": ErrorResponse, "description": "Data provider error"},
    },
    tags=["Analysis"],
    summary="Analyse a ticker symbol",
)
def analyze_ticker(request: AnalysisRequest) -> AnalysisResponse:
    """
    Fetch live market data for the supplied *ticker* and return a simple
    rule-based analysis including trend status, risk level, and advice.

    **This endpoint never executes or recommends actual trades.**
    """
    try:
        market_data = fetch_market_data(request.ticker, request.asset_type)
    except MarketDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected error fetching market data: {exc}",
        ) from exc

    return analyze(market_data)
