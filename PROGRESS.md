# Stock Mirror Fish — Project State & Progress Log
> **Read this first at the start of every new session. It is the single source of truth.**

---

## 🗂 What This App Is
A multi-agent AI stock analysis dashboard. No paid APIs — uses **yfinance** only.
- **Backend**: FastAPI (`app.py`) on `http://localhost:8080`
- **Frontend**: Single-file `dashboard.html` (vanilla JS, Chart.js)
- **GitHub**: https://github.com/abiahir/stock-mirror-fish
- **Stack**: Python 3.9+, FastAPI, yfinance, uvicorn

---

## ✅ Completed Features (DO NOT rebuild these)

### v1–v3 (done in earlier sessions)
- FastAPI backend with `/api/watchlist`, `/api/stock/{sym}`, `/api/analyze/{sym}`, `/api/heatmap`
- Four AI agents: Rex (Bull), Vera (Risk), Q (Quant), Wade (Value)
- Chart with MA20/MA50/BB Bands, timeframe selector
- 8-cell technical metrics grid (RSI, MACD, MA, Vol Z, Sortino, Calmar, CVaR, Beta)
- Council Picks table with Stop/Target/R:R/Kelly/Sortino
- Goal Tracker + Kelly Sizer + Portfolio Allocation
- Agent Discussion panel
- TTL cache (5 min, thread-safe)
- Sparkline SVGs on chips

### v4.0 (done)
- Research-grade metrics: Sortino, Calmar, CVaR 95%, Kelly (half-Kelly), Volume Z-score, ATR stops
- Sector heatmap (11 S&P sector ETFs: XLK, XLF, XLV, etc.)
- GitHub push with full README, LICENSE (MIT), CONTRIBUTING.md, .gitignore

### v4.1 (done — but has a pending bug fix, see below)
- **SSE live price stream** (`/api/stream`) — auto-reconnects, 10s market / 60s after-hours
- **Search autocomplete** — proxies Yahoo Finance search, 280ms debounce dropdown
- **Screener panel** — full-screen slide-in, filterable by score/RSI, sortable
- **Market status pill** — pre/open/closed with pulsing dot
- **Flash animations** on chips and screener rows on price change
- `_price_poller()` async task via `asyncio` + `ThreadPoolExecutor`
- `zoneinfo.ZoneInfo("America/New_York")` for market hours (no pytz needed)

---

## ✅ Bug Fixed — v4.1 (RESOLVED)

### Root Cause
In `renderChips()` (dashboard.html ~line 642):
```javascript
const srch = document.getElementById('chip-search');  // ← BUG
row.insertBefore(chip, srch);  // throws NotFoundError — srch is not a child of row
```
`#chip-search` is inside `#search-wrap` which is inside `#watchlist-row`.
`insertBefore` requires the reference node to be a **direct child** of the parent.
This throws a DOM exception → `loadWatchlist()` rejects → `Promise.all` in `init()` halts →
`selectStock()` and `startSSE()` never run → blank screen, no analysis, no live prices.

### Symptoms reported by user
- Blank screen on initial load
- Watchlist chips never appear
- Council Picks stuck on "Loading watchlist…" forever
- Search box appears empty/invisible (no chips around it)
- No live price movement visible
- Refresh button partially fixes it (re-runs selectStock manually)

### Exact Fix Needed (3 changes in dashboard.html)

**Fix 1** — `renderChips()`:
```javascript
// Change this:
const srch = document.getElementById('chip-search');
// To this:
const srch = document.getElementById('search-wrap');
```

**Fix 2** — `init()`: Make loading progressive (don't block on slow watchlist):
```javascript
async function init() {
  const DEFAULT_SYMS = 'AAPL,MSFT,NVDA,GOOGL,AMZN,META,JPM,V,TSLA,AMD,SPY,QQQ,NFLTS,BAC,DIS';
  startSSE(DEFAULT_SYMS);   // start SSE immediately with default symbols
  startCountdown();
  await Promise.all([loadHeatmap(), selectStock(S.symbol)]);  // fast first paint
  loadWatchlist();  // runs in background — slow, don't await
}
```

**Fix 3** — `startSSE()`: Accept default symbols param:
```javascript
function startSSE(defaultSyms = '') {
  if (_sse) { _sse.close(); _sse = null; }
  const syms = S.wlData.length > 0
    ? S.wlData.map(s => s.symbol).join(',')
    : (defaultSyms || S.symbol);
  _sse = new EventSource(`${BASE}/api/stream?symbols=${syms}`);
  // ... rest unchanged
}
```

**Fix 4** — `loadWatchlist()`: Restart SSE after watchlist loads (to subscribe to all symbols):
```javascript
async function loadWatchlist() {
  const data = await api('/api/watchlist');
  if (!data || !data.watchlist) return;
  S.wlData = data.watchlist;
  renderChips(data.watchlist);
  renderPicksTable(data.watchlist);
  if (S.capital > 0) renderAllocation(data.watchlist);
  startSSE();  // ← ADD THIS: restart SSE now subscribed to all watchlist symbols
}
```

**STATUS**: ✅ All four fixes applied to dashboard.html. App should now load progressively — chart and analysis appear in ~2s, chips and council picks load in background.

---

## 📁 File Structure
```
Stock Mirror Fish/
├── app.py              ← FastAPI backend (v4.1 — current, working)
├── dashboard.html      ← Frontend (v4.1 — has bug described above)
├── requirements.txt    ← pip dependencies
├── README.md           ← Full open-source README with badges
├── LICENSE             ← MIT
├── CONTRIBUTING.md     ← Fork/PR guide
├── .gitignore
├── push_to_github.bat  ← Git push helper (username: abiahir)
└── PROGRESS.md         ← This file
```

---

## 🗺 Feature Roadmap (Researched, Prioritized)

See FEATURE_ROADMAP.md for the full plan.

Priority order:
1. ~~**Fix v4.1 bugs**~~ ✅ DONE
2. **News Feed** — per-stock headlines via Yahoo Finance RSS
3. **Price Alerts** — browser notifications when price hits target/stop
4. **Earnings Calendar** — upcoming earnings dates in sidebar
5. **Portfolio P&L Tracker** — track real positions, not just recommendations
6. **Pattern Recognition** — detect chart patterns (cup & handle, head & shoulders)
7. **Multi-Timeframe Confluence** — daily + weekly signal agreement score
8. **AI Chat** — type questions to the council
9. **Backtesting** — test council picks against historical data
10. **PWA / Mobile** — make it installable on phone

---

## 🔧 How to Run

```bash
cd "Stock Mirror Fish"
pip install fastapi uvicorn yfinance pandas numpy --break-system-packages
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```
Then open: `dashboard.html` in browser (double-click or use Live Server).
No Node.js, no npm, no build step needed.

---

## 🧠 Session Rules (IMPORTANT for token efficiency)
1. **Always read this file first** before doing any work
2. **Never re-research** things already documented here
3. **One feature at a time**: research → plan → implement → test → mark done
4. **Update this file** at the end of every session with what was done
5. **Minimal API calls**: use file reads over web searches whenever possible
6. If a bug is found mid-feature, note it here and finish the feature first
