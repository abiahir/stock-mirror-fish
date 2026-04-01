<div align="center">

# 🐟 Stock Mirror Fish

### *Where four AI minds debate every stock — so you don't have to guess alone*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Yahoo Finance](https://img.shields.io/badge/Data-Yahoo%20Finance-6001D2?style=for-the-badge&logo=yahoo&logoColor=white)](https://finance.yahoo.com)
[![Chart.js](https://img.shields.io/badge/Charts-Chart.js%204-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white)](https://chartjs.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Open Source](https://img.shields.io/badge/Open%20Source-%E2%9D%A4-red?style=for-the-badge)](https://opensource.org)

**A free, open-source AI stock analysis dashboard built on research-grade risk metrics — no subscriptions, no API keys, no paywalls.**

[🚀 Quick Start](#-quick-start) · [✨ Features](#-features) · [📸 Screenshots](#-screenshots) · [🧠 The AI Council](#-the-ai-council) · [📐 Risk Metrics](#-research-grade-risk-metrics) · [🛠 Architecture](#-architecture)

---

![Stock Mirror Fish Dashboard](https://img.shields.io/badge/Status-Production%20Ready-00e676?style=for-the-badge)
![Version](https://img.shields.io/badge/Version-4.0.0-00c8ff?style=for-the-badge)
![No API Key](https://img.shields.io/badge/No%20API%20Key-Required-ffaa00?style=for-the-badge)

</div>

---

## 🌟 What is Stock Mirror Fish?

Stock Mirror Fish is a **fully local, real-time stock analysis platform** that simulates a Wall Street investment committee in your browser. Four distinct AI personas — each with their own investment philosophy — debate every stock using **institutional-grade metrics** and produce a consensus recommendation with precise entry, stop-loss, and profit targets.

> 💡 **Inspired by:** TradingView's charting · Finviz's sector heatmaps · Trade Ideas Holly AI's momentum scans · Unusual Whales' smart-money detection · Bloomberg's Sortino/CVaR standards · Prop firm Kelly Criterion sizing

---

## ✨ Features

### 🏛️ Four-Agent AI Council
| Agent | Role | Philosophy |
|-------|------|-----------|
| 🐂 **Rex** | Bull Investor | Momentum, growth, breakout detection — inspired by Trade Ideas Holly AI |
| 🐻 **Vera** | Risk Analyst | CVaR, max drawdown, prop-firm risk rules — protects capital above all |
| 📐 **Q** | Quant Analyst | Sortino, Calmar, volume Z-scores — Bloomberg-grade systematic analysis |
| 💎 **Wade** | Value Investor | FCF yield, margin analysis, moat — Buffett + Dalio methodology |

### 📊 Market Intelligence
- **🗺️ Sector Heatmap** — Finviz-style color-coded tiles for all 11 S&P sectors (XLK, XLF, XLV, XLE…)
- **✨ Sparkline Chips** — Inline SVG mini-charts on every watchlist ticker
- **🚨 Alert Badges** — Auto-flagged: `OB` (RSI>72), `OS` (RSI<30), `📊` (volume Z-score >2σ = institutional activity)
- **⏱️ Auto-Refresh** — 60-second live data cycle with countdown timer

### 📈 Advanced Charting
- **Multi-timeframe toggle** — 1M / 3M / 6M / 1Y price chart
- **MA overlays** — MA20 (gold) and MA50 (blue) always shown
- **Bollinger Bands toggle** — On/off dashed ±2σ bands overlay
- **Hover tooltips** — Price precision to the cent on any date

### 🧮 Research-Grade Risk Panel (8-cell grid)
```
RSI 14 │ MACD │ MA Signal │ Vol Z-Score
Sortino │ Calmar │ CVaR 95% │ Beta/Vol
```

### 🎯 Goal Tracker
- Enter capital ($100) + target ($200) + days (14)
- Calculates: total return needed, daily compound return, risk level, win rate required
- Generates strategy recommendation based on aggressiveness level

### 📐 Kelly Criterion Position Sizer
- Full Kelly % and Half-Kelly % (professional standard)
- Dollar amounts auto-calculated from your capital
- Win rate estimate, R/R ratio, minimum break-even win rate

### 💼 Portfolio Allocator
- Score-weighted allocation across top picks
- 20% cash buffer built in (institutional risk management standard)
- Visualized with colored allocation bars

---

## 🚀 Quick Start

### Windows (one click)
```
Double-click  ▶  start.bat
```
This auto-installs requirements, launches the server, and opens the dashboard in your browser.

### Mac / Linux
```bash
# Clone the repo
git clone https://github.com/abiahir/stock-mirror-fish.git
cd stock-mirror-fish

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py

# Open in browser
open http://localhost:8080
```

### Manual (any OS)
```bash
pip install fastapi uvicorn yfinance pandas numpy
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
# Then open http://localhost:8080 in your browser
```

**Requirements:**
- Python 3.10+
- Internet connection (for Yahoo Finance data)
- A modern browser (Chrome, Firefox, Edge)
- No API keys. No accounts. No subscriptions. 100% free.

---

## 🧠 The AI Council

Each agent scores a stock from **-100 to +100** using its own weighted criteria, then the four scores are averaged into a **consensus signal**.

### 🐂 Rex — Bull Investor
Rex hunts momentum and breakout setups. He loves:
- RSI extremes (oversold = prime buy signal 🔥)
- Strong MACD crossovers with expanding histograms
- Perfect MA stack: Price > MA20 > MA50 > MA200 (golden alignment)
- Bollinger Band squeezes (upcoming explosive move 💥)
- Volume Z-score >2.5σ (institutional accumulation 🏦)
- Revenue growth >25% YoY 🚀

### 🐻 Vera — Risk Analyst
Vera is the council's voice of caution. She monitors:
- RSI overbought signals (>78 = danger zone ⚠️)
- CVaR(95%) — the average loss in the worst 5% of days (Basel III standard)
- Maximum historical drawdown (how deep has it fallen?)
- Valuation stretch: P/E >45x = priced for perfection ❌
- Debt/Equity ratios (>300% = dangerous leverage 💀)
- Annual volatility vs position sizing rules

### 📐 Q — Quant Analyst
Q speaks only in numbers. His signals come from:
- **Sortino Ratio** >2.0 = elite (better than Sharpe — only penalises downside)
- **Calmar Ratio** >1.0 = hedge-fund acceptable (annual return / max drawdown)
- MACD histogram expansion/contraction
- Bollinger squeeze probability
- Volume Z-score 3-sigma events (near-certain institutional trigger)
- RSI statistical extremes (<25 or >80)

### 💎 Wade — Value Investor
Wade is the long-term thinker. He looks for:
- Forward P/E < Trailing P/E (earnings expanding 💎)
- P/B ratio <1.5x (near book value — asset backing)
- Net margins >28% (extraordinary moat 🏰)
- Free cash flow yield >5% (printing cash for buybacks 💰)
- Dividend yield (paid to be patient)
- Revenue growth compounding >25% YoY 🚀

---

## 📐 Research-Grade Risk Metrics

Stock Mirror Fish implements the same metrics used by hedge funds, prop firms, and institutional desks:

| Metric | Formula | Significance |
|--------|---------|-------------|
| **Sortino Ratio** | (Ann. Return − Rf) / Downside Deviation | Better than Sharpe — only penalises bad volatility |
| **Calmar Ratio** | Annual Return / Max Drawdown | Hedge fund standard; >1.0 = acceptable |
| **CVaR 95%** | Mean of worst 5% daily returns | Basel III standard; superior to VaR |
| **Kelly Criterion** | `p − (1−p)/b` | Optimal position size; Half-Kelly used for safety |
| **Volume Z-score** | `(Vol − MA20_Vol) / σ20_Vol` | Detects institutional activity (Unusual Whales method) |
| **ATR Stop-loss** | `Price − 2×ATR(14)` | Swing-trader standard (research: 2–3×ATR) |
| **Max Drawdown** | `min((Price/cummax) − 1)` | Worst peak-to-trough percentage loss |

### 🛡️ Stop-Loss Methodology
The stop-loss is calculated as the **most conservative** of three methods:
1. `Price − 2×ATR(14)` — volatility-adjusted (research standard)
2. Bollinger Lower Band (statistical support)
3. `Price × (1 − 2σ_weekly)` — weekly-volatility floor

This ensures you're never given a stop that's too loose for the asset's volatility profile.

### 🎯 Position Sizing (Half-Kelly)
```python
win_rate = 0.5 + consensus_score / 200   # [30%, 75%] range
b         = target_pct / stop_pct         # reward-to-risk
kelly     = win_rate - (1 - win_rate) / b
half_kelly = max(0, kelly / 2)            # Professional standard
```
Half-Kelly delivers ~75% of full-Kelly's growth at ~50% less drawdown — the standard at most professional trading firms.

---

## 🗺️ Architecture

```
stock-mirror-fish/
├── 📄 app.py              # FastAPI backend — all data, agents, risk metrics
├── 🌐 dashboard.html      # Single-file frontend — no build step needed
├── 📋 requirements.txt    # Python dependencies (5 packages)
├── 🚀 start.bat           # Windows one-click launcher
├── 🚀 start.sh            # Mac/Linux launcher
└── 🔧 Launch StockMirrorFish.ps1  # PowerShell launcher (spaces-safe)
```

### Backend (`app.py`)
```
FastAPI  ──►  TTL Cache (5 min, thread-safe)
          ──►  ThreadPoolExecutor (6 workers, parallel fetch)
          ──►  yfinance (Yahoo Finance, no API key)
          ──►  Technical Indicators (RSI, MACD, BB, MAs, ATR)
          ──►  Risk Metrics (Sortino, Calmar, CVaR, Kelly, Vol Z-Score)
          ──►  4 AI Agents → Discussion → Consensus → Levels
```

### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /` | GET | Serves `dashboard.html` |
| `GET /api/stock/{symbol}` | GET | Full OHLCV + all technicals + sparklines |
| `GET /api/analyze/{symbol}` | GET | 4-agent analysis + discussion + Kelly levels |
| `GET /api/watchlist` | GET | Parallel fetch of all 15 default stocks |
| `GET /api/heatmap` | GET | 11 sector ETF performance tiles |
| `GET /api/strategy` | GET | Goal-tracker calculation |
| `GET /api/health` | GET | Server health check |
| `POST /api/cache/clear` | POST | Wipe the TTL cache |

### Frontend (`dashboard.html`)
- **Zero build step** — pure HTML + CSS + vanilla JS
- **Chart.js 4** via CDN for price charts and overlays
- **Inline SVG** sparklines (no library needed)
- **CSS variables** for the full dark terminal aesthetic
- **AbortController** on every fetch (20s timeout, graceful degradation)

---

## 📸 Screenshots

> *Live dark terminal UI — inspired by Bloomberg Terminal aesthetics*

**Dashboard layout:**
- 🗺️ **Sector heatmap** strip at the top
- 📊 **Watchlist chips** with sparklines + alert badges
- 🤖 **4 agent cards** with scores, confidence bars, key points
- 💬 **Live agent debate** panel
- 📈 **Price chart** with MA overlays + BB toggle + timeframe selector
- 🧮 **8-cell metrics** grid
- 📋 **Council picks** table (sorted by consensus score)
- 🎯 **Goal tracker** + Kelly sizer + Portfolio allocator

---

## 🔧 Configuration

### Watchlist
Edit the `DEFAULT_WATCHLIST` in `app.py`:
```python
DEFAULT_WATCHLIST = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN",
    "META","JPM","V","TSLA","AMD",
    "SPY","QQQ","NFLX","BAC","DIS"
]
```

### Cache Duration
```python
CACHE_TTL = 300  # seconds (5 minutes default)
```

### Port
```python
# In start.bat / start.sh
uvicorn app:app --host 0.0.0.0 --port 8080
```

### Risk-free Rate (for Sharpe/Sortino)
```python
def calc_sharpe(returns, rf=0.05):   # Change 0.05 → your preferred RF rate
def calc_sortino(returns, rf=0.05):
```

---

## 📦 Dependencies

```
fastapi>=0.104.0        # Modern async Python web framework
uvicorn[standard]>=0.24.0  # ASGI server
yfinance>=0.2.36        # Yahoo Finance data (FREE, no API key)
pandas>=2.0.0           # Data manipulation
numpy>=1.24.0           # Numerical computation
```

All frontend libraries are loaded via CDN — no `npm install`, no webpack, no build tools.

---

## 🗺️ Roadmap

- [ ] 🔔 Price alert notifications (desktop/email)
- [ ] 📱 Mobile-responsive layout
- [ ] 🕯️ Candlestick chart mode
- [ ] 🗃️ Portfolio tracker (track actual positions)
- [ ] 📤 Export picks to CSV / PDF
- [ ] 🔌 Alpaca / Interactive Brokers paper trading integration
- [ ] 🧪 Backtesting engine (QuantConnect-style)
- [ ] 🤖 LLM-powered natural language agent commentary
- [ ] 🌐 Docker container for easy deployment
- [ ] 📊 Options flow integration (inspired by Unusual Whales)

---

## 🤝 Contributing

Contributions are welcome! Stock Mirror Fish is fully open source under the MIT License.

```bash
# Fork the repo, then:
git clone https://github.com/abiahir/stock-mirror-fish.git
cd stock-mirror-fish
git checkout -b feature/your-feature-name

# Make your changes, then:
git commit -m "✨ Add: your feature description"
git push origin feature/your-feature-name
# Open a Pull Request!
```

**Areas where contributions are especially welcome:**
- 🧮 New risk metrics or agent personas
- 📊 Additional charting overlays (VWAP, Fibonacci, etc.)
- 🌐 Internationalization (non-US markets, currency conversion)
- 🎨 UI themes or layout improvements
- 📱 Mobile responsiveness
- 🧪 Unit tests for financial calculations

---

## ⚠️ Disclaimer

> **Stock Mirror Fish is for educational and informational purposes only.**
>
> This software does **not** constitute financial advice, investment advice, or a recommendation to buy or sell any security. The AI agents, scores, and recommendations are algorithmic outputs based on publicly available market data and should not be relied upon as the sole basis for investment decisions.
>
> All investments involve risk. Past performance is not indicative of future results. Always do your own research and consult a qualified financial advisor before making investment decisions.
>
> The authors and contributors of Stock Mirror Fish are not liable for any financial losses incurred through the use of this software.

---

## 📄 License

```
MIT License — Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies — subject to the conditions in the LICENSE file.
```

See [LICENSE](LICENSE) for the full text.

---

<div align="center">

**Built with ❤️ by the open source community**

*Inspired by Bloomberg Terminal · TradingView · Finviz · Trade Ideas Holly AI · Unusual Whales*

⭐ **If Stock Mirror Fish helped you — please star the repo!** ⭐

[![GitHub stars](https://img.shields.io/github/stars/abiahir/stock-mirror-fish?style=social)](https://github.com/abiahir/stock-mirror-fish)

</div>
