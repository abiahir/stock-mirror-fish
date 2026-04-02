# Stock Mirror Fish — Feature Roadmap
> Research-first. Each feature has: Why it matters · How it works · What files change · Complexity rating

---

## 🔴 PHASE 0 — Bug Fix (Do This First)
**Fix v4.1 live data bugs** — see PROGRESS.md for exact code changes.
- Complexity: Low (3 small edits to dashboard.html)
- Blocks: Everything else depends on a working app

---

## 🟡 PHASE 1 — Stability & UX Polish

### Feature 1: Per-Stock News Feed
**Why**: Traders need to know *why* a stock is moving. Price + news together is how pros think.
**What it shows**: Latest 5 headlines for the selected stock, with source and time ago.
**How**: Yahoo Finance has a free RSS feed: `https://feeds.finance.yahoo.com/rss/2.0/headline?s=AAPL`
- Backend: `/api/news/{sym}` — fetch + parse RSS with Python's `xml.etree`, cache 10 min
- Frontend: News card at bottom of left column, appears when you select a stock
- No API key needed
**Complexity**: Low-Medium (1 new endpoint, 1 new card in HTML)
**Token cost**: ~1 session

---

### Feature 2: Price Alerts (Browser Notifications)
**Why**: Users can't watch the screen all day. Alerts let the app work *for* them.
**What it does**: User sets a price target or stop. Browser sends a desktop notification when hit.
**How**:
- Frontend only — no backend needed
- `Notification.requestPermission()` → store alerts in `S.alerts = [{sym, price, type:'above'/'below'}]`
- In `applyLivePrices()`, check each alert — if triggered, fire `new Notification(...)`
- Persist alerts in `localStorage` so they survive page reload
- UI: small bell icon in each chip, opens a mini form to set alert
**Complexity**: Low (pure frontend)
**Token cost**: ~1 session

---

### Feature 3: Earnings Calendar Sidebar Card
**Why**: Earnings are the #1 volatility event. Knowing NVDA reports in 3 days changes everything.
**What it shows**: Next 7 days of earnings for watchlist stocks, sorted by date, with expected EPS vs prior.
**How**: yfinance has `Ticker.calendar` — returns next earnings date, EPS estimate, revenue estimate
- Backend: `/api/earnings` — loops watchlist, calls `yf.Ticker(sym).calendar`, caches 1 day
- Frontend: New card in right column "📅 Earnings Calendar"
**Complexity**: Low (yfinance already has this data)
**Token cost**: ~1 session

---

## 🟠 PHASE 2 — Power User Features

### Feature 4: Portfolio P&L Tracker
**Why**: The app currently gives *recommendations*, not *reality*. A P&L tracker shows if the advice works.
**What it does**: User enters: symbol, buy price, quantity, buy date → app shows current value, P&L $, P&L %, unrealized gain, vs S&P500 benchmark.
**How**:
- Frontend only — store positions in `localStorage`
- New full card (or tab) in right column: "💼 My Portfolio"
- No backend needed — prices come from existing SSE stream
- Shows: total portfolio value, daily change, best/worst position, benchmark comparison
**Complexity**: Medium (more UI logic, localStorage schema)
**Token cost**: ~1-2 sessions

---

### Feature 5: Chart Pattern Recognition
**Why**: "Cup and handle" or "head and shoulders" patterns are what traders look for every day. Automating this is genuinely useful.
**What it detects**:
- Golden Cross / Death Cross (MA50 crosses MA200)
- Bullish/Bearish Engulfing candles
- Support/Resistance levels (price clustering)
- Volume breakout (price up + volume Z > 2)
**How**:
- Backend: Add pattern detection to `/api/analyze/{sym}` — pure Python math on existing price data
- Frontend: Show detected patterns as colored badges on the chart or in a new "Patterns" row in the technical metrics grid
**Complexity**: Medium (math logic, no new data sources)
**Token cost**: ~2 sessions

---

### Feature 6: Multi-Timeframe Confluence Score
**Why**: A signal that looks bullish on 3M but bearish on 1Y is weak. When daily + weekly + monthly all agree, that's a strong signal. This is how institutional traders filter noise.
**What it shows**: A confluence score (0-100) showing how many timeframes agree with the current signal.
- "Daily: BULL · Weekly: BULL · Monthly: BEAR → Confluence: 67% bullish"
**How**:
- Backend: Modify `/api/analyze/{sym}` to run analysis across 3 periods (1mo, 3mo, 1y) simultaneously
- Already fetches data per period — just run all 3 and compare agent scores
- New field in response: `confluence: {daily_score, weekly_score, monthly_score, agreement_pct}`
- Frontend: New row in consensus banner showing timeframe agreement
**Complexity**: Medium (parallel API calls, logic to compare)
**Token cost**: ~1 session

---

## 🟢 PHASE 3 — Advanced Features

### Feature 7: AI Chat Panel ("Ask the Council")
**Why**: Instead of reading fixed analysis, let users ask: "Why is NVDA risky right now?" or "Compare TSLA vs AAPL". This makes the AI agents feel alive.
**What it does**: Chat input at bottom of left column. User types question → agents respond with their perspective based on loaded data.
**How**:
- NO external AI API needed — responses are generated from existing analysis data using templates
- Pattern-match question intent: "why risky" → show Vera's key_points; "momentum" → Rex; "compare" → side-by-side consensus scores
- Backend: `/api/chat` endpoint — takes `{question, symbol, analysis_data}` → returns formatted response
- This can be made smarter later with an LLM API if user wants
**Complexity**: Medium-High (NLP intent matching, no external API needed for v1)
**Token cost**: ~2 sessions

---

### Feature 8: Backtesting Engine (Council vs. Reality)
**Why**: "Did my AI council's advice from 3 months ago actually make money?" This is how you build trust in any system.
**What it does**: Pick a stock, pick a date range → show what would have happened if you followed the council's buy/sell signals. Shows: win rate, avg return per trade, max drawdown, Sharpe ratio vs buy-and-hold.
**How**:
- Backend: `/api/backtest/{sym}?period=1y` — fetch historical data, run the signal logic at each point, calculate P&L
- Uses existing analysis math, just applied to historical candles
- Frontend: New panel or overlay on chart showing backtest equity curve vs buy-and-hold
**Complexity**: High (simulation logic, careful P&L math)
**Token cost**: ~3 sessions

---

### Feature 9: Market Regime Detector
**Why**: The same stock behaves differently in bull markets vs bear markets vs high-VIX environments. Knowing the regime changes which agent to trust.
**What it detects**:
- Current market regime: "Risk-On", "Risk-Off", "Trending", "Choppy", "High Volatility"
- Based on: SPY trend, VIX level (from yfinance), sector rotation, breadth
**How**:
- Backend: New `/api/regime` endpoint — analyzes SPY, VIX, sector ETF correlations
- Frontend: Regime badge in header next to market pill (replaces or complements it)
- Agents automatically adjust their confidence based on regime
**Complexity**: Medium (all data available via yfinance)
**Token cost**: ~1-2 sessions

---

### Feature 10: Progressive Web App (PWA) — Mobile Support
**Why**: A trader needs this on their phone while away from desk.
**What it adds**:
- App installs to home screen (iOS + Android)
- Works offline (shows cached last data)
- Push notifications for price alerts (using Service Worker)
- Responsive mobile layout
**How**:
- Add `manifest.json` + `service-worker.js`
- Media queries in CSS for mobile layout
- No backend changes needed
**Complexity**: Medium (Service Worker is tricky, layout rework)
**Token cost**: ~2 sessions

---

## 📊 Priority Matrix

| Feature | Impact | Complexity | Token Cost | Do When |
|---------|--------|------------|------------|---------|
| Fix v4.1 bugs | Critical | Low | 0.5 session | NOW |
| News Feed | High | Low | 1 session | Next |
| Price Alerts | High | Low | 1 session | Next |
| Earnings Calendar | Medium | Low | 1 session | Soon |
| Portfolio P&L | High | Medium | 1-2 sessions | Phase 2 |
| Pattern Recognition | Medium | Medium | 2 sessions | Phase 2 |
| Multi-TF Confluence | High | Medium | 1 session | Phase 2 |
| AI Chat | High | Med-High | 2 sessions | Phase 3 |
| Backtesting | Very High | High | 3 sessions | Phase 3 |
| Market Regime | Medium | Medium | 1-2 sessions | Phase 3 |
| PWA / Mobile | Medium | Medium | 2 sessions | Phase 3 |

---

## 📐 Design Principles (Never Break These)
1. **No paid APIs** — yfinance + Yahoo Finance free endpoints only
2. **No npm / no build step** — single HTML file, CDN scripts only
3. **One file frontend** — dashboard.html must stay self-contained
4. **Backend stays in app.py** — one Python file, no module splitting
5. **Research before code** — always document the approach before writing
6. **Don't break existing features** — each feature is additive, not replacing

---

## 🔁 Session Template (Copy-Paste for Every New Session)
```
1. Read PROGRESS.md — understand current state
2. Read FEATURE_ROADMAP.md — know the plan
3. Identify the ONE task to do this session
4. Do it: research → design → implement → test
5. Update PROGRESS.md with what changed
6. Commit to GitHub if working
```
