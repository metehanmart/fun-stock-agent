from pydantic import BaseModel, Field
from enum import Enum


class AssetType(str, Enum):
    stock = "stock"
    etf = "etf"
    index = "index"


class AnalysisRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20, examples=["AAPL"])
    asset_type: AssetType = Field(..., examples=[AssetType.stock])


class AnalysisResponse(BaseModel):
    ticker: str
    asset_type: AssetType
    company_name: str
    currency: str

    current_price: float
    change_5d_pct: float
    change_1m_pct: float
    change_3m_pct: float

    ma_50: float | None
    ma_200: float | None

    trend_status: str
    risk_level: str
    advice: str
    advice_reason: str

    disclaimer: str = (
        "This is a demo application for educational purposes only. "
        "It does not constitute financial advice and must not be used to execute trades."
    )


class ErrorResponse(BaseModel):
    detail: str
