#!/usr/bin/env python3
"""
Stock Mirror Fish v4 — Research Edition
Built on: Kelly Criterion, Sortino/Calmar/CVaR, ATR stops, sector heatmaps,
volume anomaly detection, sparklines — inspired by TradingView, Finviz,
Trade Ideas Holly AI, Unusual Whales, and Bloomberg best practices.
"""

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from concurrent.futures import ThreadPoolExecutor, as_completed
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import math, os, time, threading

app = FastAPI(title="Stock Mirror Fish", version="4.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DEFAULT_WATCHLIST = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN",
    "META","JPM","V","TSLA","AMD",
    "SPY","QQQ","NFLX","BAC","DIS"
]

# Sector ETFs — for Finviz-style heatmap
SECTOR_ETFS = {
    "Technology":       "XLK",
    "Financials":       "XLF",
    "Healthcare":       "XLV",
    "Energy":           "XLE",
    "Consumer Disc":    "XLY",
    "Staples":          "XLP",
    "Industrials":      "XLI",
    "Materials":        "XLB",
    "Real Estate":      "XLRE",
    "Utilities":        "XLU",
    "Comm Svcs":        "XLC",
}

# ─────────────────────────────────────────────
#  TTL Cache (5-minute expiry, thread-safe)
# ─────────────────────────────────────────────
_cache: dict = {}
_lock = threading.Lock()
CACHE_TTL = 300

def cache_get(key):
    with _lock:
        e = _cache.get(key)
        if e and (time.time() - e["ts"]) < CACHE_TTL:
            return e["data"]
    return None

def cache_set(key, data):
    with _lock:
        _cache[key] = {"data": data, "ts": time.time()}

def cache_clear():
    with _lock:
        _cache.clear()

# ─────────────────────────────────────────────
#  Safety helpers
# ─────────────────────────────────────────────
def safe_float(v, default=None):
    try:
        if v is None: return default
        f = float(v)
        return default if (math.isnan(f) or math.isinf(f)) else round(f, 6)
    except: return default

def safe_series_val(series, idx=-1, default=None):
    try:
        v = float(series.iloc[idx])
        return default if (math.isnan(v) or math.isinf(v)) else v
    except: return default

# ─────────────────────────────────────────────
#  Technical Indicators
# ─────────────────────────────────────────────

def calc_rsi(prices, period=14):
    try:
        d  = prices.diff()
        g  = d.where(d > 0, 0.0).rolling(period).mean()
        l  = (-d.where(d < 0, 0.0)).rolling(period).mean()
        rs = g / l
        v  = safe_series_val(100 - (100 / (1 + rs)))
        return round(v, 2) if v is not None else 50.0
    except: return 50.0

def calc_macd(prices):
    try:
        e12 = prices.ewm(span=12, adjust=False).mean()
        e26 = prices.ewm(span=26, adjust=False).mean()
        m   = e12 - e26
        s   = m.ewm(span=9, adjust=False).mean()
        h   = m - s
        mv, sv, hv = safe_series_val(m), safe_series_val(s), safe_series_val(h)
        if any(x is None for x in [mv, sv, hv]):
            return {"macd":0,"signal":0,"histogram":0,"trend":"neutral","strength":"weak"}
        return {"macd":round(mv,4),"signal":round(sv,4),"histogram":round(hv,4),
                "trend":"bullish" if mv>sv else "bearish",
                "strength":"strong" if abs(hv)>abs(mv)*0.1 else "weak"}
    except: return {"macd":0,"signal":0,"histogram":0,"trend":"neutral","strength":"weak"}

def calc_bollinger(prices, period=20):
    try:
        sma = prices.rolling(period).mean()
        std = prices.rolling(period).std()
        u, l, m = sma+2*std, sma-2*std, sma
        cur = safe_series_val(prices)
        uv,lv,mv = safe_series_val(u), safe_series_val(l), safe_series_val(m)
        if any(x is None for x in [cur,uv,lv,mv]):
            return {"upper":0,"middle":0,"lower":0,"position":0.5,"bandwidth":0.1,"squeeze":False}
        pos = (cur-lv)/(uv-lv) if (uv-lv)>0 else 0.5
        bw  = (uv-lv)/mv if mv>0 else 0.1
        return {"upper":round(uv,2),"middle":round(mv,2),"lower":round(lv,2),
                "position":round(pos,3),"bandwidth":round(bw,4),"squeeze":bw<0.04}
    except: return {"upper":0,"middle":0,"lower":0,"position":0.5,"bandwidth":0.1,"squeeze":False}

def calc_mas(prices):
    try:
        cur = safe_series_val(prices)
        def sma(n):
            v = safe_series_val(prices.rolling(n).mean())
            return round(v,2) if v is not None else None
        ma20,ma50,ma200 = sma(20),sma(50),sma(200)
        sig = "neutral"
        if cur and ma20 and ma50 and ma200:
            if   cur>ma20>ma50>ma200: sig="strong_bullish"
            elif cur>ma20 and cur>ma50: sig="bullish"
            elif cur<ma20<ma50<ma200: sig="strong_bearish"
            elif cur<ma20 and cur<ma50: sig="bearish"
        return {"ma20":ma20,"ma50":ma50,"ma200":ma200,"signal":sig,
                "golden_cross":bool(ma20 and ma50 and ma20>ma50),
                "above_ma20":bool(ma20 and cur and cur>ma20),
                "above_ma50":bool(ma50 and cur and cur>ma50),
                "above_ma200":bool(ma200 and cur and cur>ma200)}
    except: return {"ma20":None,"ma50":None,"ma200":None,"signal":"neutral",
                    "golden_cross":False,"above_ma20":False,"above_ma50":False,"above_ma200":False}

def calc_atr(hist, period=14):
    try:
        hi,lo,cl = hist["High"],hist["Low"],hist["Close"]
        pc = cl.shift(1)
        tr = pd.concat([hi-lo,(hi-pc).abs(),(lo-pc).abs()],axis=1).max(axis=1)
        v  = safe_series_val(tr.rolling(period).mean())
        return round(v,4) if v else None
    except: return None

# ── Research-grade risk metrics ──────────────────

def calc_sharpe(returns, rf=0.05):
    try:
        ann = float(returns.mean())*252 - rf
        vol = float(returns.std())*math.sqrt(252)
        return round(ann/vol, 2) if vol>0 else 0.0
    except: return 0.0

def calc_sortino(returns, rf=0.05):
    """Sortino ratio — only penalises downside volatility (better than Sharpe for safety)"""
    try:
        ann     = float(returns.mean())*252 - rf
        neg     = returns[returns < 0]
        dv      = float(neg.std())*math.sqrt(252) if len(neg)>1 else 0.001
        return round(ann/dv, 2)
    except: return 0.0

def calc_calmar(prices, returns):
    """Calmar ratio — annual return / max drawdown (hedge-fund standard)"""
    try:
        ann_ret = float(returns.mean())*252
        dd      = float(((prices/prices.cummax())-1).min())
        return round(ann_ret/abs(dd), 2) if dd < -0.001 else 0.0
    except: return 0.0

def calc_cvar(returns, confidence=0.95):
    """Conditional VaR / Expected Shortfall at 95% — Basel III standard, better than VaR"""
    try:
        n    = max(1, int(len(returns)*(1-confidence)))
        tail = sorted(returns.tolist())[:n]
        return round(float(np.mean(tail))*100, 3)
    except: return 0.0

def calc_max_drawdown(prices):
    try:
        dd = float(((prices/prices.cummax())-1).min())*100
        return round(dd, 2)
    except: return 0.0

def calc_volume_zscore(hist):
    """Volume anomaly z-score — inspired by Unusual Whales smart-money detection"""
    try:
        vol = hist["Volume"]
        m   = float(vol.rolling(20).mean().iloc[-1])
        s   = float(vol.rolling(20).std().iloc[-1])
        cur = float(vol.iloc[-1])
        return round((cur-m)/s, 2) if s>0 else 0.0
    except: return 0.0

def calc_win_rate_needed(rr_ratio):
    """Minimum win rate for break-even at given R/R ratio"""
    return round(1/(1+rr_ratio)*100, 1) if rr_ratio>0 else 50.0

# ── Kelly Criterion (Half-Kelly for safety) ────────

def estimate_kelly(avg_score, stop_pct, target_pct):
    """
    Half-Kelly position sizing — professional standard.
    Full Kelly maximises growth; half-Kelly reduces drawdown ~50% while keeping ~75% of growth.
    """
    if not stop_pct or not target_pct or stop_pct >= 0 or target_pct <= 0:
        return {"full_kelly":0, "half_kelly":0, "win_rate_est":50, "rr_ratio":0}
    win_rate = max(0.30, min(0.75, 0.5 + avg_score/200))
    avg_win  = abs(target_pct/100)
    avg_loss = abs(stop_pct/100)
    b        = avg_win/avg_loss if avg_loss>0 else 1.0
    kelly    = win_rate - (1-win_rate)/b
    half_k   = max(0.0, kelly/2)*100
    full_k   = max(0.0, kelly)*100
    return {
        "full_kelly":  round(full_k, 1),
        "half_kelly":  round(half_k, 1),
        "win_rate_est":round(win_rate*100, 1),
        "rr_ratio":    round(b, 2),
        "win_rate_needed": calc_win_rate_needed(b)
    }

# ── ATR-based stop loss (2×ATR — research standard) ──

def calc_levels(d, agents, atr):
    cp   = d.get("current_price", 0)
    if not cp: return None
    t    = d.get("technicals", {})
    bb   = t.get("bollinger", {})
    vol  = t.get("volatility_annual", 25)/100
    at   = d.get("fundamentals", {}).get("analyst_target")
    avg  = sum(a["score"] for a in agents)/max(len(agents),1)

    # Stop-loss: best of Bollinger lower or 2×ATR (research: swing traders use 2–3×ATR)
    atr_stop  = cp-(atr*2)       if atr else None
    bb_stop   = bb.get("lower")
    weekly_vol_stop = cp*(1-(vol/math.sqrt(52))*2)
    candidates = [s for s in [atr_stop, bb_stop, weekly_vol_stop] if s and 0<s<cp]
    stop  = round(max(candidates),2) if candidates else round(cp*0.93,2)
    stop_pct = round((stop/cp-1)*100, 1)

    # Price target: analyst consensus or score-weighted
    if at and at>cp:
        target = round(at, 2)
    else:
        pct = max(0.05, (avg/100)*0.30)
        target = round(cp*(1+pct), 2)
    target_pct = round((target/cp-1)*100, 1)

    risk   = abs(cp-stop)
    reward = abs(target-cp)
    rr     = round(reward/risk, 1) if risk>0 else 0

    kelly  = estimate_kelly(avg, stop_pct, target_pct)

    return {
        "stop_loss":  stop,      "stop_pct":    stop_pct,
        "target":     target,    "target_pct":  target_pct,
        "risk_reward":rr,        "kelly":       kelly,
        "risk_per_share": round(risk, 2),
        "reward_per_share": round(reward, 2),
    }

# ─────────────────────────────────────────────
#  Core Stock Data
# ─────────────────────────────────────────────

def get_stock(symbol: str, period: str = "6mo"):
    symbol = symbol.upper().strip()
    key    = f"stk:{symbol}:{period}"
    cached = cache_get(key)
    if cached: return cached

    try:
        tk   = yf.Ticker(symbol)
        hist = tk.history(period=period, timeout=15)
        info = tk.info
        if hist.empty:
            return {"error": f"No data for {symbol}"}

        prices  = hist["Close"]
        returns = prices.pct_change().dropna()
        cur     = float(prices.iloc[-1])
        prev    = float(prices.iloc[-2]) if len(prices)>1 else cur
        chg     = cur-prev
        chg_pct = (chg/prev*100) if prev else 0

        vol_t   = int(hist["Volume"].iloc[-1])
        vol_avg = int(hist["Volume"].mean())
        vr      = vol_t/vol_avg if vol_avg>0 else 1

        w52h = safe_float(info.get("fiftyTwoWeekHigh"), cur)
        w52l = safe_float(info.get("fiftyTwoWeekLow"),  cur)
        atr  = calc_atr(hist)

        # MA lines for chart overlay (90 candles)
        ma20s  = prices.rolling(20).mean().tail(90)
        ma50s  = prices.rolling(50).mean().tail(90)
        bb_obj = calc_bollinger(prices)
        bb_u   = [round(float(v),2) if not math.isnan(float(v)) else None
                  for v in (prices.rolling(20).mean()+2*prices.rolling(20).std()).tail(90)]
        bb_l   = [round(float(v),2) if not math.isnan(float(v)) else None
                  for v in (prices.rolling(20).mean()-2*prices.rolling(20).std()).tail(90)]

        chart = []
        for dt, row in hist.tail(90).iterrows():
            try:
                chart.append({"date":dt.strftime("%Y-%m-%d"),
                               "open":round(float(row["Open"]),2),
                               "high":round(float(row["High"]),2),
                               "low":round(float(row["Low"]),2),
                               "close":round(float(row["Close"]),2),
                               "volume":int(row["Volume"])})
            except: pass

        # Sparkline — last 30 closes (Finviz / TradingView pattern)
        sparkline = []
        for v in prices.tail(30).tolist():
            try:
                fv = float(v)
                if not math.isnan(fv): sparkline.append(round(fv,2))
            except: pass

        result = {
            "symbol":        symbol,
            "company_name":  info.get("longName", symbol),
            "current_price": round(cur,2),
            "change":        round(chg,2),
            "change_pct":    round(chg_pct,2),
            "volume":        vol_t,
            "avg_volume":    vol_avg,
            "vol_ratio":     round(vr,2),
            "week52_high":   round(w52h,2),
            "week52_low":    round(w52l,2),
            "from_52w_high_pct": round(((cur-w52h)/w52h*100),2) if w52h else 0,
            "sparkline":     sparkline,
            "technicals": {
                "rsi":               calc_rsi(prices),
                "macd":              calc_macd(prices),
                "bollinger":         bb_obj,
                "moving_averages":   calc_mas(prices),
                "atr":               atr,
                "sharpe_ratio":      calc_sharpe(returns),
                "sortino_ratio":     calc_sortino(returns),
                "calmar_ratio":      calc_calmar(prices, returns),
                "cvar_95":           calc_cvar(returns, 0.95),
                "max_drawdown":      calc_max_drawdown(prices),
                "volatility_annual": round(float(returns.std())*math.sqrt(252)*100,2),
                "volume_zscore":     calc_volume_zscore(hist),
                "beta":              safe_float(info.get("beta"), 1.0),
            },
            "fundamentals": {
                "pe_ratio":        safe_float(info.get("trailingPE")),
                "forward_pe":      safe_float(info.get("forwardPE")),
                "pb_ratio":        safe_float(info.get("priceToBook")),
                "market_cap":      safe_float(info.get("marketCap")),
                "revenue_growth":  safe_float(info.get("revenueGrowth")),
                "earnings_growth": safe_float(info.get("earningsGrowth")),
                "profit_margin":   safe_float(info.get("profitMargins")),
                "debt_to_equity":  safe_float(info.get("debtToEquity")),
                "current_ratio":   safe_float(info.get("currentRatio")),
                "free_cash_flow":  safe_float(info.get("freeCashflow")),
                "dividend_yield":  safe_float(info.get("dividendYield")),
                "analyst_target":  safe_float(info.get("targetMeanPrice")),
                "analyst_low":     safe_float(info.get("targetLowPrice")),
                "analyst_high":    safe_float(info.get("targetHighPrice")),
                "num_analysts":    safe_float(info.get("numberOfAnalystOpinions")),
                "sector":          info.get("sector",""),
                "industry":        info.get("industry",""),
            },
            "chart_data": chart,
            "ma20_line":  [round(float(v),2) if not math.isnan(float(v)) else None for v in ma20s],
            "ma50_line":  [round(float(v),2) if not math.isnan(float(v)) else None for v in ma50s],
            "bb_upper":   bb_u,
            "bb_lower":   bb_l,
        }
        cache_set(key, result)
        return result
    except Exception as e:
        return {"error": str(e), "symbol": symbol}

# ─────────────────────────────────────────────
#  Agent Council (4 personas)
# ─────────────────────────────────────────────

def agent_rex(d):
    """🐂 Rex — Bull. Momentum, growth, breakouts. Inspired by Trade Ideas Holly AI momentum scans."""
    score, pts = 0, []
    t, f = d.get("technicals",{}), d.get("fundamentals",{})
    rsi=t.get("rsi",50); macd=t.get("macd",{}); ma=t.get("moving_averages",{})
    bb=t.get("bollinger",{}); vz=t.get("volume_zscore",0); vr=d.get("vol_ratio",1)

    if rsi<30:  score+=30; pts.append(f"RSI {rsi:.0f} — extreme oversold, prime buy signal 🔥")
    elif rsi<45:score+=20; pts.append(f"RSI {rsi:.0f} — healthy room to run")
    elif rsi<=62:score+=12;pts.append(f"RSI {rsi:.0f} — momentum sweet spot")
    elif rsi>75: score-=5; pts.append(f"RSI {rsi:.0f} — hot, but momentum persists")

    if macd.get("trend")=="bullish":
        score+=18
        if macd.get("strength")=="strong": score+=7; pts.append("Strong MACD bullish crossover — acceleration 📈")
        else: pts.append("MACD bullish — early momentum shift")
    else: score-=8; pts.append("MACD bearish — momentum lagging")

    sig=ma.get("signal","")
    if sig=="strong_bullish": score+=28; pts.append("Perfect MA stack: price>20>50>200 ✅")
    elif sig=="bullish":      score+=18; pts.append("Price above key MAs — uptrend intact")
    elif sig=="bearish":      score-=15; pts.append("Below key MAs — trend working against us")
    elif sig=="strong_bearish":score-=25;pts.append("Death cross — breakdown in progress")

    if ma.get("golden_cross"): score+=10; pts.append("Golden cross active (20MA>50MA) 🌟")
    if bb.get("squeeze"):      score+=15; pts.append("Bollinger squeeze — explosive move building 💥")

    # Volume anomaly — Unusual Whales smart-money signal
    if vz>2.5:  score+=20; pts.append(f"Volume Z={vz:.1f} — statistically extreme institutional activity 🏦")
    elif vz>1.5:score+=12; pts.append(f"Volume Z={vz:.1f} — above-average accumulation detected")
    elif vr>1.8:score+=8;  pts.append(f"Volume {vr:.1f}x avg — elevated interest")

    rg=f.get("revenue_growth")
    if rg and rg>0.25: score+=22; pts.append(f"Revenue +{rg*100:.0f}% YoY 🚀")
    elif rg and rg>0.12:score+=14;pts.append(f"Revenue +{rg*100:.0f}% — solid growth")
    elif rg and rg<-0.05:score-=15;pts.append(f"Revenue -({abs(rg)*100:.0f}%) — headwind")

    at=f.get("analyst_target"); cp=d.get("current_price",0)
    if at and cp>0:
        up=(at-cp)/cp*100
        if up>20: score+=15; pts.append(f"Street target ${at:.0f} = {up:.0f}% upside 🎯")
        elif up>10:score+=8; pts.append(f"Analyst target ${at:.0f} = {up:.0f}% upside")

    score=max(-100,min(100,score))
    rec="Strong Buy" if score>=65 else "Buy" if score>=30 else "Hold" if score>=-10 else "Sell"
    return {"agent":"Rex","role":"Bull Investor","emoji":"🐂","color":"#00ff88",
            "score":score,"recommendation":rec,"key_points":pts[:4],"confidence":min(95,abs(score)+30),
            "personality":"Momentum-seeker. Finds opportunities where others see noise."}

def agent_vera(d):
    """🐻 Vera — Risk. CVaR, drawdown, overbought signals. Inspired by prop-firm risk rules."""
    score, pts = 0, []
    t, f = d.get("technicals",{}), d.get("fundamentals",{})
    rsi=t.get("rsi",50); vol=t.get("volatility_annual",25)
    pe=f.get("pe_ratio"); fh=d.get("from_52w_high_pct",0)
    d2e=f.get("debt_to_equity"); margin=f.get("profit_margin")
    max_dd=t.get("max_drawdown",0); cvar=t.get("cvar_95",0)
    sortino=t.get("sortino_ratio",0)

    if rsi>78:   score-=30; pts.append(f"RSI {rsi:.0f} — dangerously overbought ⚠️")
    elif rsi>68: score-=16; pts.append(f"RSI {rsi:.0f} — overheating, late-cycle risk")
    elif rsi<35: score+=15; pts.append(f"RSI {rsi:.0f} — oversold, capitulation likely done")
    else:        score+=5;  pts.append(f"RSI {rsi:.0f} — within normal range")

    if pe and pe>45:  score-=28; pts.append(f"P/E {pe:.0f}x — priced for perfection ❌")
    elif pe and pe>32:score-=16; pts.append(f"P/E {pe:.0f}x — stretched, no error margin")
    elif pe and pe<14:score+=22; pts.append(f"P/E {pe:.0f}x — deep value territory 💎")
    elif pe and pe<20:score+=12; pts.append(f"P/E {pe:.0f}x — fair value, comfortable")

    # CVaR risk assessment (Basel III standard)
    if cvar and cvar<-3: score-=20; pts.append(f"CVaR(95%) {cvar:.2f}% — extreme tail risk 🔴")
    elif cvar and cvar<-1.5:score-=10;pts.append(f"CVaR(95%) {cvar:.2f}% — elevated tail risk")
    elif cvar and cvar>-0.5:score+=8; pts.append(f"CVaR(95%) {cvar:.2f}% — tail risk contained ✓")

    # Max drawdown history
    if max_dd<-40:  score-=18; pts.append(f"Max drawdown {max_dd:.0f}% — deep historical pain")
    elif max_dd>-15:score+=10; pts.append(f"Max drawdown only {abs(max_dd):.0f}% — historically resilient")

    if d2e and d2e>300:score-=25;pts.append(f"D/E {d2e:.0f}% — dangerous leverage 💀")
    elif d2e and d2e>150:score-=12;pts.append(f"D/E {d2e:.0f}% — elevated debt load")
    elif d2e and d2e<30:score+=12; pts.append(f"D/E {d2e:.0f}% — fortress balance sheet 🏰")

    if vol>60:  score-=22; pts.append(f"{vol:.0f}% annual vol — extreme, position small")
    elif vol>40:score-=12; pts.append(f"{vol:.0f}% annual vol — elevated, monitor closely")
    elif vol<20:score+=10; pts.append(f"{vol:.0f}% vol — low-vol quality name")

    if fh>-3:   score-=16; pts.append("Near 52-week high — limited upside, high reversal risk")
    elif fh<-35:score+=12; pts.append(f"{abs(fh):.0f}% off 52w high — beaten down")

    if margin and margin>0.22: score+=12; pts.append(f"{margin*100:.0f}% margin — durable pricing power 💪")
    elif margin and margin<0.03:score-=18;pts.append(f"Only {margin*100:.1f}% margin — dangerously thin")

    if not pts: pts.append("No critical red flags — risk profile acceptable"); score+=8
    score=max(-100,min(100,score))
    rec="Buy" if score>=30 else "Hold" if score>=-10 else "Reduce" if score>=-40 else "Sell"
    return {"agent":"Vera","role":"Risk Analyst","emoji":"🐻","color":"#ff4466",
            "score":score,"recommendation":rec,"key_points":pts[:4],"confidence":min(95,abs(score)+25),
            "personality":"Protects capital above all. CVaR & drawdown are her primary lenses."}

def agent_q(d):
    """📐 Q — Quant. Sortino, Calmar, Sharpe, volume Z-score. Bloomberg/QuantConnect-grade metrics."""
    score, pts = 0, []
    t=d.get("technicals",{})
    sharpe=t.get("sharpe_ratio",0); sortino=t.get("sortino_ratio",0)
    calmar=t.get("calmar_ratio",0); macd=t.get("macd",{})
    bb=t.get("bollinger",{}); ma=t.get("moving_averages",{})
    rsi=t.get("rsi",50); vz=t.get("volume_zscore",0)
    cvar=t.get("cvar_95",0)

    # Sortino — better than Sharpe for downside risk (research finding)
    if sortino>2.0:  score+=38; pts.append(f"Sortino {sortino:.2f} — elite downside-adjusted alpha 🏆")
    elif sortino>1.5:score+=30; pts.append(f"Sortino {sortino:.2f} — excellent downside protection")
    elif sortino>1.0:score+=20; pts.append(f"Sortino {sortino:.2f} — strong risk-adjusted return")
    elif sortino>0.5:score+=10; pts.append(f"Sortino {sortino:.2f} — positive but modest")
    elif sortino<0:  score-=20; pts.append(f"Sortino {sortino:.2f} — downside risk not rewarded 📉")

    # Calmar — hedge fund standard (annual return / max drawdown)
    if calmar>2.0:  score+=20; pts.append(f"Calmar {calmar:.2f} — returns handsomely exceed drawdown risk")
    elif calmar>1.0:score+=12; pts.append(f"Calmar {calmar:.2f} — return justifies drawdown (>1.0 threshold)")
    elif calmar>0:  score+=5;  pts.append(f"Calmar {calmar:.2f} — marginal, borderline acceptable")
    elif calmar<0:  score-=15; pts.append(f"Calmar {calmar:.2f} — losing money on a drawdown-adjusted basis")

    # MACD histogram
    h=macd.get("histogram",0)
    if h>0 and macd.get("trend")=="bullish": score+=15; pts.append("MACD histogram expanding — momentum confirmed")
    elif h<0 and macd.get("trend")=="bearish":score-=12;pts.append("MACD histogram negative — momentum fading")

    # Bollinger squeeze
    if bb.get("squeeze"): score+=22; pts.append("BB squeeze → breakout imminent 💥 (~68% historical accuracy)")

    # Volume z-score (Unusual Whales methodology)
    if vz>2.5:   score+=22; pts.append(f"Vol Z={vz:.1f} — 3-sigma event, institutional-grade signal")
    elif vz>1.5: score+=14; pts.append(f"Vol Z={vz:.1f} — significant above-average activity")
    elif vz<-1.5:score-=8;  pts.append(f"Vol Z={vz:.1f} — below-average conviction")

    # MA alignment
    sig=ma.get("signal","")
    if "bullish" in sig: score+=18; pts.append(f"MA: {sig.replace('_',' ')} — systematic trend positive")
    elif "bearish" in sig:score-=15;pts.append(f"MA: {sig.replace('_',' ')} — trend signal negative")

    # RSI extremes
    if rsi<25:  score+=18; pts.append(f"RSI {rsi:.0f} — statistically extreme oversold")
    elif rsi>80:score-=18; pts.append(f"RSI {rsi:.0f} — statistically extreme overbought")

    score=max(-100,min(100,score))
    rec="Strong Buy" if score>=65 else "Buy" if score>=30 else "Hold" if score>=-10 else "Sell"
    return {"agent":"Q","role":"Quant Analyst","emoji":"📐","color":"#4488ff",
            "score":score,"recommendation":rec,"key_points":pts[:4],"confidence":min(95,abs(score)+35),
            "personality":"Data only. Sortino, Calmar, CVaR, volume Z-scores. No opinions."}

def agent_wade(d):
    """💎 Wade — Value. FCF yield, Calmar fundamentals, margin analysis. Buffett + Dalio approach."""
    score, pts = 0, []
    f=d.get("fundamentals",{})
    pe=f.get("pe_ratio"); fpe=f.get("forward_pe"); pb=f.get("pb_ratio")
    margin=f.get("profit_margin"); rg=f.get("revenue_growth")
    dy=f.get("dividend_yield"); at=f.get("analyst_target")
    fcf=f.get("free_cash_flow"); mc=f.get("market_cap")
    cp=d.get("current_price",0); d2e=f.get("debt_to_equity")

    if fpe and pe:
        if fpe<pe*0.8: score+=25; pts.append(f"Forward P/E {fpe:.1f}x < trailing {pe:.0f}x — earnings expanding 💎")
        if fpe<18:     score+=15; pts.append(f"Forward P/E {fpe:.1f}x — attractive for growth profile")
    elif pe:
        if pe<13:   score+=25; pts.append(f"P/E {pe:.0f}x — deep value, earnings cheap")
        elif pe<20: score+=14; pts.append(f"P/E {pe:.0f}x — fair price for quality")
        elif pe>40: score-=18; pts.append(f"P/E {pe:.0f}x — priced for decades of perfection")

    if pb and pb<1.5: score+=18; pts.append(f"P/B {pb:.1f}x — near book value, asset backing solid 🔍")

    if margin and margin>0.28: score+=25; pts.append(f"{margin*100:.0f}% net margin — extraordinary moat 🏰")
    elif margin and margin>0.16:score+=15;pts.append(f"{margin*100:.0f}% margin — durable profitability")
    elif margin and margin<0.03:score-=20;pts.append(f"Only {margin*100:.1f}% margin — commoditised, fragile")

    if rg and rg>0.25: score+=25; pts.append(f"+{rg*100:.0f}% revenue growth — compounding machine 🚀")
    elif rg and rg>0.12:score+=16;pts.append(f"+{rg*100:.0f}% revenue — healthy trajectory")
    elif rg and rg<-0.08:score-=22;pts.append(f"Revenue -({abs(rg)*100:.0f}%) — structural decline")

    # Free cash flow yield (institutional quality metric)
    if fcf and mc and mc>0:
        fy=fcf/mc*100
        if fy>5:  score+=18; pts.append(f"{fy:.1f}% FCF yield — printing cash, buyback/dividend fuel 💰")
        elif fy>2:score+=8;  pts.append(f"{fy:.1f}% FCF yield — positive generation")
        elif fy<0:score-=12; pts.append("Negative FCF — burning cash, sustainability risk")

    if dy and dy>0.03: score+=12; pts.append(f"{dy*100:.1f}% dividend — paid to be patient")

    if at and cp>0:
        up=(at-cp)/cp*100
        if up>25: score+=15; pts.append(f"Consensus target ${at:.0f} = {up:.0f}% upside")

    if not pts: pts.append("Insufficient fundamental data"); score=0
    score=max(-100,min(100,score))
    rec="Strong Buy" if score>=55 else "Buy" if score>=22 else "Hold" if score>=-12 else "Sell"
    return {"agent":"Wade","role":"Value Investor","emoji":"💎","color":"#ffaa00",
            "score":score,"recommendation":rec,"key_points":pts[:4],"confidence":min(95,abs(score)+20),
            "personality":"Long-term, quality-focused. FCF yield and moat analysis are paramount."}

# ─────────────────────────────────────────────
#  Discussion Generator
# ─────────────────────────────────────────────

def gen_discussion(sym, d, agents):
    msgs = []
    rex  = next(a for a in agents if a["agent"]=="Rex")
    vera = next(a for a in agents if a["agent"]=="Vera")
    q    = next(a for a in agents if a["agent"]=="Q")
    wade = next(a for a in agents if a["agent"]=="Wade")
    t,f  = d.get("technicals",{}), d.get("fundamentals",{})
    rsi=t.get("rsi",50); macd=t.get("macd",{}); ma=t.get("moving_averages",{})
    sortino=t.get("sortino_ratio",0); calmar=t.get("calmar_ratio",0)
    cvar=t.get("cvar_95",0); vz=t.get("volume_zscore",0)
    pe=f.get("pe_ratio"); cp=d.get("current_price",0); at=f.get("analyst_target")
    margin=f.get("profit_margin"); rg=f.get("revenue_growth")
    bb=t.get("bollinger",{}); vol=t.get("volatility_annual",25)
    name=d.get("company_name",sym); fh=d.get("from_52w_high_pct",0)

    # Rex opens
    r = f"Opening on {sym} — {name}. "
    if rex["score"]>50:
        r += "Setup looks strong. "
        sig=ma.get("signal","")
        if "strong_bullish" in sig: r += "MAs perfectly aligned — price above 20, 50, 200-day. "
        if macd.get("trend")=="bullish" and macd.get("strength")=="strong": r += "MACD crossing bullish with force. "
        if vz>1.5: r += f"Volume Z={vz:.1f} — institutional-scale activity. "
        r += f"Rex: {rex['score']}/100 → {rex['recommendation']}."
    elif rex["score"]>15:
        r += f"Constructive but mixed. RSI {rsi:.0f}, MACD {macd.get('trend','neutral')}, MAs {ma.get('signal','neutral').replace('_',' ')}. "
        r += f"Potential here. {rex['score']}/100 → {rex['recommendation']}."
    else:
        r += f"Weak momentum. RSI {rsi:.0f}, MAs {ma.get('signal','bearish').replace('_',' ')}. "
        r += f"Trend is not our friend. {rex['score']}/100 → {rex['recommendation']}."
    msgs.append({"agent":"Rex","emoji":"🐂","color":rex["color"],"message":r})

    # Vera on risk
    v = ""
    if vera["score"]<-25:
        v = "Rex, pump the brakes. "
        risks=[]
        if pe and pe>35: risks.append(f"P/E {pe:.0f}x leaves zero margin for error")
        if rsi>68: risks.append(f"RSI {rsi:.0f} — chasing overbought")
        if fh>-4: risks.append("near 52-week high — asymmetric downside")
        if cvar and cvar<-2: risks.append(f"CVaR(95%) at {cvar:.2f}% — tail risk is real")
        if risks: v += "Key concerns: "+"; ".join(risks[:3])+". "
        v += f"Vera: {vera['score']}/100 → {vera['recommendation']}."
    elif vera["score"]>10:
        v = f"Not sounding alarm bells today. "
        if cvar and cvar>-1: v += f"CVaR(95%) at {cvar:.2f}% — tail risk contained. "
        v += f"{vol:.0f}% annual vol is manageable. {vera['recommendation']}."
    else:
        v = f"Risk profile: {vol:.0f}% annual vol. "
        if cvar: v += f"CVaR(95%) {cvar:.2f}%. "
        if pe: v += f"P/E {pe:.0f}x. "
        v += f"Vera: {vera['score']}/100 → {vera['recommendation']}."
    msgs.append({"agent":"Vera","emoji":"🐻","color":vera["color"],"message":v})

    # Q with advanced metrics
    qm = "Quantitative picture: "
    qm += f"Sortino ratio {sortino:.2f} "
    if sortino>1.5: qm += "(elite — downside risk is handsomely rewarded). "
    elif sortino>1: qm += "(solid — we're compensated for the downside). "
    elif sortino<0: qm += "(negative — risk is NOT rewarded. Hard pass from the model). "
    else: qm += "(marginal). "
    if calmar>1: qm += f"Calmar {calmar:.2f} — annual return exceeds max drawdown, hedge-fund acceptable. "
    elif calmar<0: qm += f"Calmar {calmar:.2f} — returns don't justify the drawdown. "
    if bb.get("squeeze"): qm += "Bollinger squeeze active — models flag imminent directional move. "
    if vz>2: qm += f"Volume Z={vz:.1f} — 3-sigma event, near-certain institutional trigger. "
    qm += f"Q: {q['score']}/100 → {q['recommendation']}."
    msgs.append({"agent":"Q","emoji":"📐","color":q["color"],"message":qm})

    # Wade on fundamentals
    wm = f"Business fundamentals: "
    if wade["score"]>35:
        wm += "Quality business. "
        quals=[]
        if margin and margin>0.15: quals.append(f"{margin*100:.0f}% net margins signal a moat")
        if rg and rg>0.10: quals.append(f"revenue +{rg*100:.0f}% — compounding")
        if at and cp and (at-cp)/cp>0.15: quals.append(f"analysts see {((at-cp)/cp*100):.0f}% upside")
        if quals: wm += "; ".join(quals[:3])+". "
        wm += f"Comfortable owning this. Wade: {wade['score']}/100 → {wade['recommendation']}."
    elif wade["score"]<-20:
        wm += "Fundamentals give me pause. "
        if wade["key_points"]: wm += wade["key_points"][0]+". "
        wm += f"Wade: {wade['score']}/100 → {wade['recommendation']}."
    else:
        wm += f"Decent business, fair price. "
        if pe: wm += f"P/E {pe:.0f}x. "
        wm += f"Wade: {wade['score']}/100 → {wade['recommendation']}."
    msgs.append({"agent":"Wade","emoji":"💎","color":wade["color"],"message":wm})

    # Debate if divergent
    scores=[a["score"] for a in agents]
    avg=sum(scores)/len(scores); spread=max(scores)-min(scores)
    if spread>55:
        db=f"Council split: {spread:.0f}-point spread. Rex at {rex['score']:+.0f} vs Vera at {vera['score']:+.0f}. "
        db+="When technicals say buy but risk says no — size smaller than usual, use a tight stop."
        msgs.append({"agent":"Debate","emoji":"⚖️","color":"#aa44ff","message":db,"is_debate":True})

    # Consensus
    if avg>45:
        cm=f"🎯 CONSENSUS BULLISH — {avg:.0f}/100. "
        if at and cp: cm+=f"Street target ${at:.0f} = {((at-cp)/cp*100):.0f}% upside. "
        cm+="Recommended allocation: 20-30% of capital. Set 2×ATR stop."
    elif avg>18:
        cm=f"🎯 CONSENSUS CONSTRUCTIVE — {avg:.0f}/100. Add on weakness. Allocation: 10-18%."
    elif avg>-12:
        cm=f"🎯 CONSENSUS NEUTRAL — {avg:.0f}/100. Mixed signals. Hold; wait for catalyst."
    else:
        cm=f"🎯 CONSENSUS CAUTIOUS — {avg:.0f}/100. Risk/reward unfavourable. Allocation: 0%."
    msgs.append({"agent":"Consensus","emoji":"🎯","color":"#ffffff","message":cm,
                 "is_consensus":True,"score":round(avg,1)})
    return msgs

# ─────────────────────────────────────────────
#  API Endpoints
# ─────────────────────────────────────────────

@app.get("/api/stock/{symbol}")
def api_stock(symbol: str, period: str = "6mo"):
    d = get_stock(symbol, period)
    if "error" in d: return JSONResponse(d, status_code=404)
    return d

@app.get("/api/analyze/{symbol}")
def analyze(symbol: str):
    key = f"ana:{symbol.upper()}"
    cached = cache_get(key)
    if cached: return cached

    d = get_stock(symbol)
    if "error" in d: return JSONResponse(d, status_code=404)

    agents     = [agent_rex(d), agent_vera(d), agent_q(d), agent_wade(d)]
    discussion = gen_discussion(symbol, d, agents)
    avg        = sum(a["score"] for a in agents)/len(agents)
    atr        = d.get("technicals",{}).get("atr")
    levels     = calc_levels(d, agents, atr)

    if avg>50:   ov,oc="Strong Buy","#00ff88"
    elif avg>20: ov,oc="Buy","#44cc77"
    elif avg>-10:ov,oc="Hold","#ffaa00"
    elif avg>-30:ov,oc="Reduce","#ff6644"
    else:        ov,oc="Sell","#ff2244"

    result={"symbol":symbol.upper(),"company_name":d.get("company_name",symbol),
            "current_price":d.get("current_price"),"change_pct":d.get("change_pct"),
            "technicals":d.get("technicals",{}),"fundamentals":d.get("fundamentals",{}),
            "agents":agents,"discussion":discussion,"levels":levels,
            "consensus":{"score":round(avg,1),"recommendation":ov,"color":oc,
                         "confidence":min(95,int(abs(avg)*0.8+30))}}
    cache_set(key, result)
    return result

def _wl_item(sym):
    try:
        d=get_stock(sym,"3mo")
        if "error" in d: return None
        agents=[agent_rex(d),agent_vera(d),agent_q(d),agent_wade(d)]
        avg=sum(a["score"] for a in agents)/len(agents)
        atr=d.get("technicals",{}).get("atr")
        levels=calc_levels(d,agents,atr)
        if avg>50: rec="Strong Buy"
        elif avg>20:rec="Buy"
        elif avg>-10:rec="Hold"
        elif avg>-30:rec="Reduce"
        else:rec="Sell"
        t=d.get("technicals",{})
        return {"symbol":sym,"company_name":d.get("company_name",sym),
                "price":d.get("current_price"),"change_pct":d.get("change_pct"),
                "score":round(avg,1),"recommendation":rec,
                "volatility":t.get("volatility_annual"),"sharpe":t.get("sharpe_ratio"),
                "sortino":t.get("sortino_ratio"),"calmar":t.get("calmar_ratio"),
                "rsi":t.get("rsi"),"volume_zscore":t.get("volume_zscore"),
                "sector":d.get("fundamentals",{}).get("sector",""),
                "market_cap":d.get("fundamentals",{}).get("market_cap"),
                "levels":levels,"sparkline":d.get("sparkline",[])}
    except: return None

@app.get("/api/watchlist")
def watchlist(symbols: str = ""):
    syms=[s.strip().upper() for s in symbols.split(",") if s.strip()] if symbols else DEFAULT_WATCHLIST
    key=f"wl:{','.join(syms)}"
    cached=cache_get(key)
    if cached: return cached
    results=[]
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures={ex.submit(_wl_item,sym):sym for sym in syms}
        for fut in as_completed(futures):
            r=fut.result()
            if r: results.append(r)
    data={"watchlist":sorted(results,key=lambda x:x.get("score",0),reverse=True),
          "timestamp":datetime.now().isoformat(),"count":len(results)}
    cache_set(key,data)
    return data

def _sector_item(args):
    sector, etf = args
    try:
        d = get_stock(etf, "5d")
        if "error" in d: return None
        t = d.get("technicals",{})
        return {"sector":sector,"symbol":etf,
                "change_pct":d.get("change_pct",0),
                "price":d.get("current_price"),
                "volume_zscore":t.get("volume_zscore",0),
                "rsi":t.get("rsi",50)}
    except: return None

@app.get("/api/heatmap")
def sector_heatmap():
    """Finviz-style sector performance heatmap"""
    key="heatmap"
    cached=cache_get(key)
    if cached: return cached
    results=[]
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures={ex.submit(_sector_item,(s,e)):s for s,e in SECTOR_ETFS.items()}
        for fut in as_completed(futures):
            r=fut.result()
            if r: results.append(r)
    data={"heatmap":sorted(results,key=lambda x:x.get("change_pct",0),reverse=True),
          "timestamp":datetime.now().isoformat()}
    cache_set(key,data)
    return data

@app.get("/api/strategy")
def strategy(capital:float=1000, target:float=2000, days:int=14):
    req=(target/capital-1)*100
    daily=((target/capital)**(1/days)-1)*100
    if req>100 and days<=7:   risk,note="Extreme ⚠️⚠️","Near-impossible returns required. Likely outcome is significant capital loss. Extend timeline substantially."
    elif req>60 and days<=14: risk,note="Very High ⚠️","Aggressive but attempted. Use only highest-conviction momentum plays. Strict 2×ATR stops. Half-Kelly sizing only."
    elif req>25:              risk,note="High","Ambitious. Focus top 3-4 picks. Fixed fractional at 1-2% per trade max."
    elif req>10:              risk,note="Moderate","Achievable with discipline. Diversify 4-6 positions. Quality over quantity."
    else:                     risk,note="Low-Moderate","Conservative target. Blue-chips or index ETFs will get you there safely."

    wl=watchlist()
    top=[s for s in wl.get("watchlist",[]) if s.get("score",0)>5]
    pcts=[0.35,0.25,0.20,0.12,0.08]
    allocs=[]
    for s,pct in zip(top[:5],pcts):
        lvl=s.get("levels") or {}
        sp=lvl.get("stop_pct"); tp=lvl.get("target_pct")
        avg_score=s.get("score",0)
        kelly=estimate_kelly(avg_score, sp, tp)
        allocs.append({"symbol":s["symbol"],"company_name":s.get("company_name",""),
                       "allocation_pct":round(pct*100,1),"allocation_amount":round(capital*pct,2),
                       "score":s.get("score",0),"recommendation":s.get("recommendation",""),
                       "stop_loss":lvl.get("stop_loss"),"stop_pct":sp,
                       "target":lvl.get("target"),"target_pct":tp,
                       "risk_reward":lvl.get("risk_reward"),
                       "kelly":kelly,
                       "sortino":s.get("sortino"),"calmar":s.get("calmar"),
                       "rationale":f"Score {s['score']:.0f}/100 — {s['recommendation']}"})
    return {"capital":capital,"target":target,"days":days,
            "required_return_pct":round(req,1),"daily_return_needed_pct":round(daily,3),
            "risk_level":risk,"risk_note":note,"allocations":allocs,
            "summary":f"Need {req:.1f}% total ({daily:.3f}%/day) over {days} days."}

@app.post("/api/cache/clear")
def clear_cache():
    cache_clear()
    return {"status":"cleared","ts":datetime.now().isoformat()}

@app.get("/api/health")
def health():
    return {"status":"ok","version":"4.0.0","cache_keys":len(_cache),
            "watchlist_size":len(DEFAULT_WATCHLIST),"sectors":len(SECTOR_ETFS),
            "ts":datetime.now().isoformat()}

@app.get("/")
def root():
    if os.path.exists("dashboard.html"):
        return FileResponse("dashboard.html")
    return {"status":"Stock Mirror Fish v4 — Research Edition","docs":"/docs"}

if __name__=="__main__":
    import uvicorn
    print("\n"+"="*58)
    print("  🐟  STOCK MIRROR FISH  v4  — Research Edition")
    print("="*58)
    print(f"  📊  Dashboard  → http://localhost:8080")
    print(f"  📡  API Docs   → http://localhost:8080/docs")
    print(f"  💊  Health     → http://localhost:8080/api/health")
    print(f"  🗺   Heatmap   → http://localhost:8080/api/heatmap")
    print(f"  📈  Tracking {len(DEFAULT_WATCHLIST)} stocks + {len(SECTOR_ETFS)} sector ETFs")
    print(f"  🧠  Risk: Kelly·Sortino·Calmar·CVaR·ATR-Stop")
    print("="*58+"\n")
    uvicorn.run(app, host="0.0.0.0", port=8080, timeout_keep_alive=30)
