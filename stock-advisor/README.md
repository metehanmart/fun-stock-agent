# Stock Advisor Demo

A simple, **educational** backend application that fetches live market data and
returns a rule-based analysis for stocks, ETFs/funds, and market indexes.

> ⚠️ **Disclaimer:** This application is for demonstration and educational
> purposes only. It does **not** constitute financial advice and must **never**
> be used to execute real trades.

---

## Features

| Feature | Details |
|---|---|
| Asset types | Stock, ETF / Fund, Index |
| Price data | Live quotes via [yfinance](https://github.com/ranaroussi/yfinance) |
| Metrics | Current price, 5-day / 1-month / 3-month change %, 50-day MA, 200-day MA |
| Analysis | Trend status, risk level, advice (Buy / Hold / Watch / Avoid) |
| API | FastAPI with automatic OpenAPI docs |

---

## Project Structure

```
stock-advisor/
├── main.py                  # FastAPI application & route definitions
├── models/
│   └── schemas.py           # Pydantic request / response models
├── services/
│   ├── market_data.py       # yfinance data fetching & normalisation
│   └── analyzer.py          # Rule-based analysis engine
├── requirements.txt
└── README.md
```

---

## Getting Started

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the development server

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

---

## API Reference

Interactive docs (Swagger UI) are served automatically at:

```
http://127.0.0.1:8000/docs
```

### Endpoints

#### `GET /`
Health-check — confirms the API is running.

#### `GET /asset-types`
Returns the list of supported asset type values to populate a UI dropdown.

#### `POST /analyze`
Analyses a ticker symbol and returns a full report.

**Request body:**

```json
{
  "ticker": "AAPL",
  "asset_type": "stock"
}
```

**`asset_type` values:** `stock` | `etf` | `index`

**Example tickers:**

| Symbol | Asset type |
|---|---|
| `AAPL` | stock |
| `MSFT` | stock |
| `QQQM` | etf |
| `SPY` | etf |
| `^IXIC` | index |
| `^NDX` | index |
| `^GSPC` | index |

**Response (200 OK):**

```json
{
  "ticker": "AAPL",
  "asset_type": "stock",
  "company_name": "Apple Inc.",
  "currency": "USD",
  "current_price": 213.49,
  "change_5d_pct": 1.24,
  "change_1m_pct": -3.87,
  "change_3m_pct": 6.15,
  "ma_50": 210.30,
  "ma_200": 198.75,
  "trend_status": "Strong uptrend",
  "risk_level": "Medium",
  "advice": "Hold",
  "advice_reason": "Mixed signals — some positive momentum but not yet a clear breakout...",
  "disclaimer": "This is a demo application for educational purposes only..."
}
```

---

## Analysis Logic

The analysis engine is intentionally simple and transparent.

### Momentum score (−3 → +3)
Each timeframe (5-day, 1-month, 3-month) contributes **+1** if the change is
positive or **−1** if negative.

### Moving-average score (−2 → +2)
- **+1** if price > 50-day MA
- **+1** if price > 200-day MA
- Negative equivalents apply when price is below each MA.

### Total score → Advice

| Total score | Advice |
|---|---|
| ≥ 3 | **Buy** |
| 1 – 2 | **Hold** |
| 0 | **Watch** |
| ≤ −1 | **Avoid** |

> A *Buy* signal is automatically downgraded to *Watch* when volatility is
> classified as **High**, adding an extra layer of caution.

### Risk level

Derived from the average absolute swing across the three timeframes, adjusted
by asset class (indexes and ETFs have lower thresholds than individual stocks).

| Avg absolute swing | Risk |
|---|---|
| Low | Low |
| Medium | Medium |
| High | High |
