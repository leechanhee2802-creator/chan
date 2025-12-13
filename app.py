import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import json
import re
from datetime import datetime

# =========================
# OpenAI (Responses API)
# =========================
# requirements.txt: openai>=1.40 권장
from openai import OpenAI


# =====================================
# 페이지 설정
# =====================================
st.set_page_config(
    page_title="내 주식 자동판독기 (시장 개요 + 레이어/갭/ATR/장중 흐름)",
    page_icon="📈",
    layout="wide",
)

# =====================================
# 전체 스타일 (라이트 고정 + 모바일 글씨 가독성)
# =====================================
st.markdown(
    """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

html, body, [data-testid="stAppViewContainer"] {
    font-family: "Pretendard", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    color: #111827;
    background-color: #ffffff;
    color-scheme: light;
    -webkit-text-size-adjust: 100% !important;
}

/* 전체 배경: 옅은 그라데이션 */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #f4f7ff 0%, #eefdfd 50%, #fdfcfb 100%);
}

/* 메인 컨테이너 폭 */
main.block-container {
    max-width: 1250px;
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}

/* 헤더/사이드바는 흰색 */
header, [data-testid="stHeader"], [data-testid="stSidebar"] {
    background-color: #ffffff !important;
}

/* Expander */
[data-testid="stExpander"], [data-testid="stExpander"] > details,
[data-testid="stExpander"] details > summary, [data-testid="stExpander"] details > div {
    background-color: #ffffff !important;
    color: #111827 !important;
}
[data-testid="stExpander"] summary { color: #111827 !important; }

/* 제목들 */
h1 { font-size: 1.6rem; font-weight: 700; color: #111827 !important; }
h2 { font-size: 1.25rem; font-weight: 600; color: #111827 !important; }
h3 { font-size: 1.05rem; font-weight: 600; color: #111827 !important; }

/* 기본 텍스트 */
p, label, span, div { font-size: 0.94rem; color: #111827 !important; }

/* 얇은 캡션 */
.small-muted { font-size: 0.8rem; color: #6b7280 !important; }

/* 카드 */
.card-soft {
    background: rgba(255, 255, 255, 0.96);
    border-radius: 20px;
    padding: 14px 18px;
    box-shadow: 0 10px 25px rgba(15, 23, 42, 0.08);
    border: 1px solid #e5e7eb;
    margin-bottom: 12px;
}
.card-soft-sm {
    background: rgba(255, 255, 255, 0.96);
    border-radius: 18px;
    padding: 10px 14px;
    box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
    border: 1px solid #e5e7eb;
    margin-bottom: 10px;
}

/* 칩 */
.chip {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.84rem;
    font-weight: 600;
}
.chip-green { background: #bbf7d0; color: #166534 !important; }
.chip-blue  { background: #dbeafe; color: #1d4ed8 !important; }
.chip-red   { background: #fee2e2; color: #b91c1c !important; }

/* 레이어 제목 */
.layer-title-en {
    font-size: 0.85rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #6b7280 !important;
    margin-bottom: 4px;
}

/* 레이어 행 */
.layer-row { display:flex; justify-content:space-between; align-items:center; margin-top:4px; }
.layer-symbol { font-weight:600; font-size:0.95rem; color:#111827 !important; }
.layer-chg-pos { font-weight:600; font-size:0.95rem; color:#dc2626 !important; } /* 빨강 */
.layer-chg-neg { font-weight:600; font-size:0.95rem; color:#2563eb !important; } /* 파랑 */
.layer-chg-flat{ font-weight:600; font-size:0.95rem; color:#4b5563 !important; }

/* metric 카드 */
.metric-card {
    background: rgba(255, 255, 255, 0.96);
    border-radius: 20px;
    padding: 12px 16px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
    margin-bottom: 8px;
}
.metric-label { font-size:0.8rem; font-weight:500; color:#6b7280 !important; }
.metric-value { font-size:1.3rem; font-weight:700; margin-top:4px; color:#111827 !important; }
.metric-delta-pos {
    display:inline-flex; align-items:center; margin-top:6px;
    padding:2px 8px; border-radius:999px;
    background:#bbf7d0; color:#166534 !important;
    font-size:0.78rem; font-weight:600;
}
.metric-delta-neg {
    display:inline-flex; align-items:center; margin-top:6px;
    padding:2px 8px; border-radius:999px;
    background:#fee2e2; color:#b91c1c !important;
    font-size:0.78rem; font-weight:600;
}

/* 입력 */
[data-baseweb="input"] > div, [data-baseweb="select"] > div {
    background-color:#ffffff !important;
    border-radius:999px !important;
    border:1px solid #e5e7eb !important;
}
[data-baseweb="input"] input, textarea {
    background-color:transparent !important;
    color:#111827 !important;
}
textarea { border-radius:16px !important; }
input::placeholder, textarea::placeholder { color:#9ca3af !important; }

/* 버튼 */
.stButton>button {
    border-radius: 999px;
    padding: 6px 16px;
    border: 1px solid #e5e7eb;
    background: #ffffff;
    font-size: 0.92rem;
    font-weight: 500;
    color: #111827 !important;
}
.stButton>button:hover {
    border-color: #4f46e5;
    background: #eef2ff;
}

/* 모바일 */
@media (max-width: 768px) {
    .metric-value { font-size: 1.4rem; }
    .layer-symbol, .layer-chg-pos, .layer-chg-neg, .layer-chg-flat { font-size: 1.0rem; }
}
</style>
""",
    unsafe_allow_html=True,
)

# =====================================
# 한글 이름 → 티커 매핑
# =====================================
KOREAN_TICKER_MAP = {
    "엔비디아": "NVDA", "엔비디아코퍼레이션": "NVDA",
    "마이크로소프트": "MSFT", "마소": "MSFT",
    "애플": "AAPL",
    "테슬라": "TSLA",
    "아마존": "AMZN", "아마존닷컴": "AMZN",
    "구글": "GOOGL", "알파벳": "GOOGL", "알파벳A": "GOOGL", "알파벳C": "GOOG",
    "메타": "META", "페이스북": "META",
    "넷플릭스": "NFLX",
    "슈퍼마이크로": "SMCI", "슈퍼마이크로컴퓨터": "SMCI",
    "팔란티어": "PLTR",
    "브로드컴": "AVGO",
    "에이엠디": "AMD", "AMD": "AMD",
    "TSMC": "TSM", "티에스엠씨": "TSM",

    "오라클": "ORCL",
    "페이팔": "PYPL",

    "QQQ": "QQQ", "나스닥ETF": "QQQ", "나스닥100": "QQQ",
    "SPY": "SPY", "S&P500": "SPY", "SP500": "SPY",
    "VOO": "VOO",

    "SOXL": "SOXL", "반도체3배": "SOXL",
    "SOXS": "SOXS", "반도체인버스3배": "SOXS",
    "TQQQ": "TQQQ", "나스닥3배": "TQQQ",
    "SQQQ": "SQQQ", "나스닥인버스3배": "SQQQ",
    "TECL": "TECL", "기술주3배": "TECL",
    "SPXL": "SPXL", "S&P3배": "SPXL",
    "SPXS": "SPXS", "S&P인버스3배": "SPXS",
    "LABU": "LABU", "바이오3배": "LABU",
    "LABD": "LABD", "바이오인버스3배": "LABD",

    "비트코인ETF": "IBIT",
    "아이쉐어즈비트코인": "IBIT",
}

POPULAR_SYMBOLS = [
    "NVDA", "META", "TSLA", "AAPL", "MSFT", "AMZN",
    "QQQ", "TQQQ", "SOXL", "SPY", "VOO",
    "ORCL", "PYPL", "NFLX", "PLTR", "AVGO",
]

SCAN_CANDIDATES = sorted(set(POPULAR_SYMBOLS + ["GOOGL"]))


def normalize_symbol(user_input: str) -> str:
    name = (user_input or "").strip()
    if name in KOREAN_TICKER_MAP:
        return KOREAN_TICKER_MAP[name]
    return name.replace(" ", "").upper()


# =====================================
# 외부 지표 함수들
# =====================================
def fetch_fgi():
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        data = r.json()
        series = data.get("fear_and_greed_historical", {}).get("data", [])
        if not series:
            return None
        last_point = series[-1]
        return float(last_point.get("y"))
    except Exception:
        return None


def get_usdkrw_rate():
    try:
        ticker = yf.Ticker("USDKRW=X")
        df = ticker.history(period="1d")
        if df.empty:
            return 1350.0
        return float(df["Close"].iloc[-1])
    except Exception:
        return 1350.0


def get_last_extended_price(symbol: str):
    try:
        t = yf.Ticker(symbol)
        df = t.history(period="1d", interval="1m", auto_adjust=False, prepost=True)
        if df.empty:
            return None
        return float(df["Close"].iloc[-1])
    except Exception:
        return None


def safe_last_change_info(ticker_str: str):
    try:
        info = yf.Ticker(ticker_str).info
        last = info.get("regularMarketPrice")
        prev = info.get("regularMarketPreviousClose")
        market_state = info.get("marketState", "")
        if last is None or prev in (None, 0, 0.0):
            return None, None, market_state
        chg_pct = (last - prev) / prev * 100
        return float(last), float(chg_pct), market_state
    except Exception:
        return None, None, ""


def get_etf_price_with_prepost(symbol: str, name: str):
    try:
        t = yf.Ticker(symbol)
        info = t.info
        market_state = info.get("marketState", "")
        prev_close = info.get("regularMarketPreviousClose")
        pre = info.get("preMarketPrice")
        post = info.get("postMarketPrice")
        regular = info.get("regularMarketPrice")

        current = None
        chg_pct = None
        basis = "기준 불명"

        if market_state == "PRE" and pre is not None:
            current = pre
            basis = "프리장 기준"
            chg_pct = info.get("preMarketChangePercent")
            if chg_pct is None and prev_close not in (None, 0, 0.0):
                chg_pct = (pre - prev_close) / prev_close * 100
        elif market_state == "POST" and post is not None:
            current = post
            basis = "애프터장 기준"
            chg_pct = info.get("postMarketChangePercent")
            if chg_pct is None and prev_close not in (None, 0, 0.0):
                chg_pct = (post - prev_close) / prev_close * 100
        elif regular is not None:
            current = regular
            basis = "정규장 기준"
            chg_pct = info.get("regularMarketChangePercent")
            if chg_pct is None and prev_close not in (None, 0, 0.0):
                chg_pct = (regular - prev_close) / prev_close * 100

        if current is None:
            current = pre or post or regular

        return {
            "symbol": symbol,
            "name": name,
            "current": float(current) if current is not None else None,
            "basis": basis,
            "chg_pct": float(chg_pct) if chg_pct is not None else None,
            "market_state": market_state,
        }
    except Exception:
        return {"symbol": symbol, "name": name, "current": None, "basis": "조회 실패", "chg_pct": None, "market_state": ""}


BIGTECH_LIST = [
    ("NVDA", "NVDA"),
    ("AAPL", "AAPL"),
    ("MSFT", "MSFT"),
    ("AMZN", "AMZN"),
    ("META", "META"),
    ("GOOGL", "GOOGL"),
    ("TSLA", "TSLA"),
]

SECTOR_ETF_LIST = [
    ("기술주 (XLK)", "XLK"),
    ("반도체 (SOXX)", "SOXX"),
    ("금융 (XLF)", "XLF"),
    ("헬스케어 (XLV)", "XLV"),
    ("에너지 (XLE)", "XLE"),
    ("커뮤니케이션 (XLC)", "XLC"),
]


@st.cache_data(ttl=60)
def get_us_market_overview():
    overview = {}

    nq_last, nq_chg, nq_state = safe_last_change_info("NQ=F")
    es_last, es_chg, es_state = safe_last_change_info("ES=F")
    overview["futures"] = {
        "nasdaq": {"last": nq_last, "chg_pct": nq_chg, "state": nq_state},
        "sp500": {"last": es_last, "chg_pct": es_chg, "state": es_state},
    }

    tnx_last, tnx_chg, tnx_state = safe_last_change_info("^TNX")
    if tnx_last is not None:
        us10y = tnx_last / 10.0
        us10y_chg = tnx_chg / 10.0 if tnx_chg is not None else None
    else:
        us10y, us10y_chg = None, None

    dxy_last, dxy_chg, dxy_state = safe_last_change_info("DX-Y.NYB")

    overview["rates_fx"] = {
        "us10y": us10y,
        "us10y_chg": us10y_chg,
        "us10y_state": tnx_state,
        "dxy": dxy_last,
        "dxy_chg": dxy_chg,
        "dxy_state": dxy_state,
    }

    overview["etfs"] = [
        get_etf_price_with_prepost("QQQ", "QQQ (나스닥100 ETF)"),
        get_etf_price_with_prepost("VOO", "VOO (S&P500 ETF)"),
        get_etf_price_with_prepost("SOXX", "SOXX (반도체 ETF)"),
    ]

    overview["fgi"] = fetch_fgi()

    bigtech = []
    score_bt = 0
    for sym, _ in BIGTECH_LIST:
        _, chg, _ = safe_last_change_info(sym)
        if chg is not None:
            if chg >= 1:
                score_bt += 1
            elif chg <= -1:
                score_bt -= 1
        bigtech.append({"symbol": sym, "chg": chg})
    overview["bigtech"] = {"score": score_bt, "items": bigtech}

    sector = []
    score_sec = 0
    for label, sym in SECTOR_ETF_LIST:
        _, chg, _ = safe_last_change_info(sym)
        if chg is not None:
            if chg >= 0.8:
                score_sec += 1
            elif chg <= -0.8:
                score_sec -= 1
        sector.append({"label": label, "symbol": sym, "chg": chg})
    overview["sector"] = {"score": score_sec, "items": sector}

    return overview


def compute_market_score(overview: dict):
    if not overview:
        return 0, "데이터 부족", "실시간 시장 데이터를 불러오지 못했습니다."

    fut = overview.get("futures", {})
    rf = overview.get("rates_fx", {})
    etfs = overview.get("etfs", [])

    score = 0
    details = []

    nas = fut.get("nasdaq", {})
    nas_chg = nas.get("chg_pct")
    if nas_chg is not None:
        if nas_chg >= 1.0:
            score += 2; details.append(f"나스닥 선물 +{nas_chg:.2f}% (강한 상승)")
        elif nas_chg >= 0.3:
            score += 1; details.append(f"나스닥 선물 +{nas_chg:.2f}% (완만한 상승)")
        elif nas_chg <= -1.0:
            score -= 2; details.append(f"나스닥 선물 {nas_chg:.2f}% (강한 하락)")
        elif nas_chg <= -0.3:
            score -= 1; details.append(f"나스닥 선물 {nas_chg:.2f}% (완만한 하락)")

    us10y = rf.get("us10y")
    if us10y is not None:
        if us10y < 4.0:
            score += 2; details.append(f"미 10년물 {us10y:.2f}% (금리 우호)")
        elif us10y < 4.2:
            score += 1; details.append(f"미 10년물 {us10y:.2f}% (무난)")
        elif us10y > 4.4:
            score -= 2; details.append(f"미 10년물 {us10y:.2f}% (금리 부담)")
        else:
            score -= 1; details.append(f"미 10년물 {us10y:.2f}% (다소 부담)")

    dxy = rf.get("dxy")
    if dxy is not None:
        if dxy < 104:
            score += 1; details.append(f"DXY {dxy:.2f} (달러 약세 → Risk-on 우호)")
        elif dxy > 106:
            score -= 1; details.append(f"DXY {dxy:.2f} (달러 강세 → Risk-off 경계)")

    for e in etfs:
        sym = e.get("symbol")
        chg = e.get("chg_pct")
        if chg is None:
            continue
        if chg >= 0.5:
            score += 1; details.append(f"{sym} +{chg:.2f}% (ETF 강세)")
        elif chg <= -0.5:
            score -= 1; details.append(f"{sym} {chg:.2f}% (ETF 약세)")

    if score >= 5:
        label = "🚀 강한 Risk-on (상승장 상단 구간)"
    elif score >= 2:
        label = "😊 약한 Risk-on ~ 우상향 기대"
    elif score >= -1:
        label = "😐 중립/혼조 (방향 모호)"
    elif score >= -4:
        label = "⚠ 약한 Risk-off (조정/변동성 주의)"
    else:
        label = "🧨 강한 Risk-off (공포장 가능성)"

    return score, label, " · ".join(details)


# =====================================
# 가격 데이터 + 지표
# =====================================
@st.cache_data(ttl=300)
def get_price_data(symbol, period="6mo"):
    if not symbol:
        return pd.DataFrame()
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval="1d", auto_adjust=False)
    except Exception:
        return pd.DataFrame()
    if df.empty:
        return df
    return df[["Open", "High", "Low", "Close", "Volume"]].dropna()


def add_indicators(df: pd.DataFrame):
    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    df["MA5"] = close.rolling(5).mean()
    ma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    df["MA20"] = ma20
    df["BBL"] = ma20 - 2 * std20
    df["BBU"] = ma20 + 2 * std20

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_SIGNAL"] = df["MACD"].ewm(span=9, adjust=False).mean()

    low14 = low.rolling(14).min()
    high14 = high.rolling(14).max()
    denom = (high14 - low14).replace(0, np.nan)
    df["STOCH_K"] = (close - low14) / denom * 100
    df["STOCH_D"] = df["STOCH_K"].rolling(3).mean()

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    roll_up = gain.ewm(alpha=1 / 14, adjust=False).mean()
    roll_down = loss.ewm(alpha=1 / 14, adjust=False).mean()
    rs = roll_up / roll_down
    df["RSI14"] = 100 - (100 / (1 + rs))

    df["MA50"] = close.rolling(50).mean()

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["ATR14"] = tr.rolling(14).mean()

    return df.dropna()


@st.cache_data(ttl=120)
def get_intraday_5m(symbol: str):
    try:
        t = yf.Ticker(symbol)
        df = t.history(period="2d", interval="5m", auto_adjust=False, prepost=False)
        if df.empty:
            return pd.DataFrame()
        return df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    except Exception:
        return pd.DataFrame()


# =====================================
# 코멘트/판단 함수
# =====================================
def short_term_bias(last_row):
    price = float(last_row["Close"])
    ma5 = float(last_row["MA5"])
    ma20 = float(last_row["MA20"])
    macd = float(last_row["MACD"])
    macds = float(last_row["MACD_SIGNAL"])
    rsi = float(last_row["RSI14"])
    k = float(last_row["STOCH_K"])
    d = float(last_row["STOCH_D"])

    score = 0
    score += 1 if price > ma20 else -1
    score += 1 if price > ma5 else -1
    score += 1 if macd > macds else -1

    if rsi > 60:
        score += 1
    elif rsi < 40:
        score -= 1

    if k > d and k > 50:
        score += 1
    elif k < d and k < 50:
        score -= 1

    if score >= 3:
        return "단기 상방 우세 (며칠 내 상승 압력이 상대적으로 큼)"
    elif score <= -3:
        return "단기 하방 우세 (며칠 내 조정/하락 압력이 큼)"
    else:
        return "단기 중립~혼조 (방향성이 뚜렷하지 않음)"


def get_mode_config(mode_name: str):
    if mode_name == "단타":
        return {"name": "단타", "period": "3mo", "lookback_short": 10, "lookback_long": 20, "atr_mult": 1.0}
    elif mode_name == "장기":
        return {"name": "장기", "period": "1y", "lookback_short": 20, "lookback_long": 60, "atr_mult": 1.6}
    else:
        return {"name": "스윙", "period": "6mo", "lookback_short": 15, "lookback_long": 40, "atr_mult": 1.3}


def calc_trend_stops(df: pd.DataFrame, cfg: dict):
    if df.empty:
        return None, None
    last = df.iloc[-1]
    price = float(last["Close"])
    ma20 = float(last["MA20"])
    atr = float(last["ATR14"]) if "ATR14" in last and not np.isnan(last["ATR14"]) else None

    recent_short = df.tail(cfg["lookback_short"])
    recent_long = df.tail(cfg["lookback_long"])

    swing_low = float(recent_short["Low"].min())
    box_low = float(recent_long["Low"].min())

    candidates = []
    if swing_low < price:
        candidates.append(swing_low * 0.995)
    if ma20 < price:
        candidates.append(ma20 * 0.99)
    if box_low < price:
        candidates.append(box_low * 0.995)
    if atr is not None and atr > 0:
        atr_stop = price - cfg["atr_mult"] * atr
        if atr_stop < price:
            candidates.append(atr_stop)

    if not candidates:
        return None, None

    sl0 = max(candidates)

    deep_candidate = min(box_low * 0.985, swing_low * 0.985)
    sl1 = min(sl0 * 0.97, deep_candidate)

    return sl0, sl1


def calc_trend_targets(df: pd.DataFrame, cfg: dict):
    if df.empty:
        return None, None, None
    last = df.iloc[-1]
    price = float(last["Close"])
    bbu = float(last["BBU"])
    rsi = float(last["RSI14"])

    recent_short = df.tail(cfg["lookback_short"])
    recent_long = df.tail(cfg["lookback_long"])

    swing_high = float(recent_short["High"].max())
    box_high = float(recent_long["High"].max())

    base_res = max(swing_high * 0.995, box_high * 0.99)
    if not np.isnan(bbu):
        base_res = max(base_res, bbu * 0.98)

    tp1 = base_res if base_res > price else price * 1.08
    tp0 = price + (tp1 - price) * 0.6
    tp2 = tp1 + (tp1 - price) * 0.7

    if rsi > 70:
        tp0 = price + (tp1 - price) * 0.5
        tp2 = tp1 + (tp1 - price) * 0.4

    return tp0, tp1, tp2


def calc_levels(df, last, cfg):
    if df.empty:
        return (None,) * 7

    price = float(last["Close"])
    ma20 = float(last["MA20"])
    bbl = float(last["BBL"])

    if price > ma20:
        buy_low = ma20 * 0.98
        buy_high = ma20 * 1.01
    else:
        buy_low = bbl * 0.98
        buy_high = bbl * 1.02

    tp0, tp1, tp2 = calc_trend_targets(df, cfg)
    sl0, sl1 = calc_trend_stops(df, cfg)

    return buy_low, buy_high, tp0, tp1, tp2, sl0, sl1


def calc_gap_info(df: pd.DataFrame):
    if len(df) < 2:
        return None, None
    prev_close = float(df["Close"].iloc[-2])
    today_open = float(df["Open"].iloc[-1])
    gap_pct = (today_open - prev_close) / prev_close * 100
    if gap_pct > 1.5:
        comment = "강한 갭상 출발 (상승 모멘텀 강함, 갭 메움 체크 필요)"
    elif gap_pct > 0.3:
        comment = "완만한 갭상 출발 (긍정적 시초 분위기)"
    elif gap_pct < -1.5:
        comment = "강한 갭하 출발 (위험, 공포성 매도 가능)"
    elif gap_pct < -0.3:
        comment = "완만한 갭하 출발 (조정성 출발)"
    else:
        comment = "갭 거의 없음 (중립적 시초)"
    return gap_pct, comment


def get_intraday_5m_score(df_5m: pd.DataFrame):
    if df_5m.empty:
        return None, "5분봉 데이터 부족"

    last = df_5m.iloc[-1]
    price = float(last["Close"])

    last50 = df_5m.tail(50)
    ma20_5m = last50["Close"].rolling(20).mean().iloc[-1]

    score = 0
    details = []

    if price > ma20_5m:
        score += 1
        details.append("5분봉 기준 단기 상방 유지")
    else:
        details.append("5분봉 기준 단기 하락/조정")

    last10 = df_5m.tail(10)
    up_cnt = (last10["Close"] > last10["Open"]).sum()
    if up_cnt >= 6:
        score += 1
        details.append(f"최근 10개 캔들 중 {up_cnt}개 상승 (매수 우위)")
    else:
        details.append(f"최근 10개 캔들 중 상승 {up_cnt}개")

    vol_recent = last50["Volume"]
    med_vol = vol_recent.median()
    today_vol = last["Volume"]
    if med_vol > 0 and today_vol > med_vol * 1.3:
        score += 1
        details.append("최근 대비 5분봉 거래량 급증")
    else:
        details.append("5분봉 거래량 평이")

    if len(df_5m) >= 2:
        prev = df_5m.iloc[-2]
        if price > prev["Close"]:
            score += 1
            details.append("직전 봉 대비 가격 상승")
        else:
            details.append("직전 봉 대비 가격 약화")

    if score >= 3:
        comment = "장중 매수세 우위 (단타/추세 이어질 가능성↑)"
    elif score == 2:
        comment = "장중 약한 매수 우세 혹은 혼조"
    elif score == 1:
        comment = "매수/매도 힘 균형, 뚜렷한 방향성 약함"
    else:
        comment = "장중 매도 우위 또는 관망 권장"

    return score, comment + " / " + " · ".join(details)


def make_signal(last, holding_type, fgi, tp1, sl0):
    """
    단순하고 일관된 행동 신호:
    - 보유/신규 모두 공통 규칙 기반
    """
    price = float(last["Close"])
    ma20 = float(last["MA20"])
    macd = float(last["MACD"])
    macds = float(last["MACD_SIGNAL"])
    rsi = float(last["RSI14"])
    bbu = float(last["BBU"])
    k = float(last["STOCH_K"])
    d = float(last["STOCH_D"])
    bbl = float(last["BBL"])

    fear = (fgi is not None and fgi <= 25)
    greed = (fgi is not None and fgi >= 75)

    trend_up = (price > ma20 and macd > macds and rsi >= 45)
    strong_overbought = (price > bbu and k > 80 and rsi > 65 and macd < macds)
    strong_oversold = (price < bbl and k < 20 and d < 20 and rsi < 35)

    broken = (sl0 is not None and price < sl0 * 0.995)
    near_tp = (tp1 is not None and price >= tp1 * 0.95)

    if holding_type == "보유 중":
        if broken:
            return "손절 or 비중축소 (주요 지지/추세 이탈)"
        if tp1 is not None and price >= tp1 * 0.98 and strong_overbought:
            return "강한 부분매도 (저항+과열)"
        if near_tp and (rsi > 70 or price > ma20):
            return "부분매도 (저항 부근)"
        if strong_oversold and not broken:
            return "합리적 분할매수 (과매도 반등 가능)"
        if trend_up:
            return "보유/추세 유지 (상방 추세)"
        return "관망 (애매 구간)"
    else:
        # 신규 진입
        if fear and strong_oversold:
            return "초기 매수 관심 (공포+과매도)"
        if strong_oversold:
            return "초기 매수 관심 (과매도)"
        if trend_up and rsi < 65:
            return "조건부 진입 가능 (추세는 우호)"
        if greed and rsi > 70:
            return "관망 (과열/탐욕 구간)"
        return "관망 (신규 진입 관점)"


# =====================================
# 신규 진입 스캐너 (A안: 심플 + 결과 접기)
# =====================================
def scan_new_entry_candidates(cfg: dict, max_results: int = 8):
    results = []

    ov = get_us_market_overview()
    market_score, _, _ = compute_market_score(ov)

    for sym in SCAN_CANDIDATES:
        df = get_price_data(sym, cfg["period"])
        if df.empty:
            continue
        df = add_indicators(df)
        if df.empty or len(df) < max(30, cfg["lookback_long"] + 5):
            continue

        last = df.iloc[-1]
        price = float(last["Close"])
        rsi = float(last["RSI14"])

        buy_low, buy_high, tp0, tp1, tp2, sl0, sl1 = calc_levels(df, last, cfg)
        if buy_low is None or buy_high is None:
            continue

        band_center = (buy_low + buy_high) / 2
        dist_band_pct = abs(price - band_center) / price * 100

        if price < buy_low * 0.97 or price > buy_high * 1.05:
            continue
        if rsi > 65:
            continue

        bias = short_term_bias(last)
        score = 0
        if "상방" in bias:
            score += 2
        elif "중립" in bias:
            score += 1

        score += max(0, 3 - dist_band_pct)
        score += max(0, 2 - abs(rsi - 50) / 10)

        results.append(
            {
                "symbol": sym,
                "price": price,
                "rsi": rsi,
                "bias": bias,
                "dist_band": dist_band_pct,
                "buy_low": buy_low,
                "buy_high": buy_high,
                "tp1": tp1,
                "sl0": (buy_low * 0.97),
                "score": score,
            }
        )

    results_sorted = sorted(results, key=lambda x: x["score"], reverse=True)
    return market_score, results_sorted[:max_results]


# =====================================
# GPT(=AI) 자동분석: JSON 스키마 + 파싱
# =====================================
AI_JSON_SCHEMA = {
    "one_line": "한 줄 결론 (1문장, 명령형/행동형)",
    "confusing_zone": "헷갈리는 구간 설명 (3~6줄)",
    "if_then_cards": [
        {"if": "조건", "then": "행동", "note": "짧은 이유/주의"}
    ],
    "market_tone": "시장 톤 조절 (Risk-on/off를 반영한 2~4줄)",
    "questions": [
        "사용자에게 되묻는 질문 1개",
        "사용자에게 되묻는 질문 1개"
    ],
    "guardrails": [
        "이 분석이 틀릴 수 있는 이유 1",
        "추가 확인해야 할 데이터 1"
    ]
}

def _extract_json(text: str):
    """
    모델이 앞뒤로 설명을 섞어도 JSON만 뽑아내기 위해:
    1) ```json ... ``` 블록 우선
    2) 없으면 첫 { ... } 덩어리 추출 시도
    """
    if not text:
        return None

    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S | re.I)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass

    # 가장 바깥 { } 덩어리 찾기 (단순)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        chunk = text[start:end+1]
        try:
            return json.loads(chunk)
        except Exception:
            return None
    return None


def call_ai_auto_analysis(
    symbol: str,
    holding_type: str,
    mode_name: str,
    market_score: int,
    fgi,
    price: float,
    levels: dict,
    indicators: dict,
    signal: str,
    bias_comment: str,
):
    """
    ✅ Responses API (response_format 사용 X)
    ✅ JSON은 프롬프트로 강제
    """
    api_key = st.secrets.get("OPENAI_API_KEY", None)
    if not api_key:
        return None, "OPENAI_API_KEY가 설정되지 않았습니다. (Streamlit secrets에 추가 필요)"

    client = OpenAI(api_key=api_key)

    # 프롬프트: JSON만 출력 강제
    prompt = f"""
너는 한국어로 답하는 '주식 자동판독기'의 AI 분석 엔진이다.
아래 입력을 바탕으로 반드시 **JSON만** 출력해라.
- 설명 문장/서론/마크다운/코드블록 금지
- 출력은 JSON 객체 1개만
- 숫자는 필요하면 소수 2자리로
- 과장 금지, 판단 근거는 짧고 명확하게
- 투자 조언처럼 단정하지 말고 '조건부/확률/리스크'를 포함해라

반드시 아래 스키마 형태로 출력:
{json.dumps(AI_JSON_SCHEMA, ensure_ascii=False, indent=2)}

[입력]
- 티커: {symbol}
- 보유 상태: {holding_type}
- 모드: {mode_name}
- 시장점수: {market_score} (범위 -8~+8)
- 공포탐욕지수(FGI): {fgi}
- 현재가: {price:.2f}
- 추천 액션(기술적): {signal}
- 단기 방향성: {bias_comment}

[레벨]
- buy_low: {levels.get("buy_low")}
- buy_high: {levels.get("buy_high")}
- tp0: {levels.get("tp0")}
- tp1: {levels.get("tp1")}
- tp2: {levels.get("tp2")}
- sl0: {levels.get("sl0")}
- sl1: {levels.get("sl1")}

[지표]
- RSI14: {indicators.get("rsi")}
- MACD: {indicators.get("macd")}
- MACD_SIGNAL: {indicators.get("macds")}
- MA20: {indicators.get("ma20")}
- MA50: {indicators.get("ma50")}
- ATR14: {indicators.get("atr14")}
- STOCH_K: {indicators.get("k")}
- STOCH_D: {indicators.get("d")}

출력은 JSON만.
"""

    try:
        resp = client.responses.create(
            model="gpt-5-mini",
            input=prompt,
            max_output_tokens=650,
        )
        text = resp.output_text
        data = _extract_json(text)
        if data is None:
            return None, "AI 응답에서 JSON 파싱 실패 (모델이 형식을 어겼습니다)."
        return data, None
    except Exception as e:
        return None, f"AI 호출 실패: {e}"


# =====================================
# 세션 상태
# =====================================
if "recent_symbols" not in st.session_state:
    st.session_state["recent_symbols"] = []
if "favorite_symbols" not in st.session_state:
    st.session_state["favorite_symbols"] = []
if "selected_symbol" not in st.session_state:
    st.session_state["selected_symbol"] = "엔비디아"
if "run_from_side" not in st.session_state:
    st.session_state["run_from_side"] = False
if "symbol_input" not in st.session_state:
    st.session_state["symbol_input"] = st.session_state["selected_symbol"]
if "pending_symbol" not in st.session_state:
    st.session_state["pending_symbol"] = ""
if "scroll_to_result" not in st.session_state:
    st.session_state["scroll_to_result"] = False
if "scan_results" not in st.session_state:
    st.session_state["scan_results"] = None

if st.session_state.get("pending_symbol"):
    ps = st.session_state["pending_symbol"]
    st.session_state["symbol_input"] = ps
    st.session_state["selected_symbol"] = ps
    st.session_state["run_from_side"] = True
    st.session_state["pending_symbol"] = ""


# =====================================
# 레이아웃
# =====================================
col_main, col_side = st.columns([3, 1])

# ---- 오른쪽: 즐겨찾기 / 최근검색 ----
with col_side:
    st.subheader("⭐ 즐겨찾기 & 최근 종목")
    tab_fav, tab_recent = st.tabs(["⭐ 즐겨찾기", "🕒 최근 검색"])
    clicked_symbol = None

    with tab_fav:
        favs = st.session_state["favorite_symbols"]
        if not favs:
            st.caption("아직 즐겨찾기한 종목이 없습니다.")
        else:
            for sym in favs:
                if st.button(sym, key=f"fav_{sym}"):
                    clicked_symbol = sym

    with tab_recent:
        recents = list(reversed(st.session_state["recent_symbols"]))
        if not recents:
            st.caption("최근 조회 종목이 없습니다.")
        else:
            for sym in recents:
                if st.button(sym, key=f"recent_{sym}"):
                    clicked_symbol = sym

    if clicked_symbol:
        st.session_state["selected_symbol"] = clicked_symbol
        st.session_state["symbol_input"] = clicked_symbol
        st.session_state["run_from_side"] = True

# ---- 왼쪽: 메인 ----
with col_main:
    st.title("📈 내 주식 자동판독기")
    st.caption("시장 개요 + 개별 종목 판독 + 레이어/갭/ATR/장중 흐름 + AI 자동분석(옵션)")

    # 1) 시장 개요
    with st.expander("🌍 미국 시장 실시간 흐름 (보조지표 + 레이어)", expanded=True):
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            refresh = st.button("🔄 새로고침", key="refresh_overview")
        if refresh:
            get_us_market_overview.clear()

        with st.spinner("미국 선물 · 금리 · 달러 · ETF · 레이어 불러오는 중..."):
            ov = get_us_market_overview()

        score_mkt, label_mkt, detail_mkt = compute_market_score(ov)

        fut = ov.get("futures", {})
        rf = ov.get("rates_fx", {})
        etfs = ov.get("etfs", [])
        bigtech_layer = ov.get("bigtech", {})
        sector_layer = ov.get("sector", {})

        nas = fut.get("nasdaq", {})
        es = fut.get("sp500", {})

        col1, col2, col3 = st.columns(3)
        with col1:
            last = nas.get("last"); chg = nas.get("chg_pct")
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">나스닥 선물</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{last:.1f}</div>' if last is not None else '<div class="metric-value">N/A</div>', unsafe_allow_html=True)
            if chg is not None:
                st.markdown(f'<div class="metric-delta-pos">↑ {chg:.2f}%</div>' if chg >= 0 else f'<div class="metric-delta-neg">↓ {abs(chg):.2f}%</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            last = es.get("last"); chg = es.get("chg_pct")
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">S&P500 선물</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{last:.1f}</div>' if last is not None else '<div class="metric-value">N/A</div>', unsafe_allow_html=True)
            if chg is not None:
                st.markdown(f'<div class="metric-delta-pos">↑ {chg:.2f}%</div>' if chg >= 0 else f'<div class="metric-delta-neg">↓ {abs(chg):.2f}%</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">시장 점수</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{score_mkt} / 8</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="small-muted">{label_mkt}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.caption("※ 범위: -8 ~ 8 | 선물·금리·달러·ETF 기준 종합")

        if detail_mkt:
            st.caption("· " + detail_mkt)

        st.markdown("---")

        col4, col5, col6 = st.columns(3)
        with col4:
            us10y = rf.get("us10y"); us10y_chg = rf.get("us10y_chg")
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">미 10년물</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{us10y:.2f}%</div>' if us10y is not None else '<div class="metric-value">N/A</div>', unsafe_allow_html=True)
            if us10y_chg is not None:
                st.markdown(f'<div class="metric-delta-pos">▲ {us10y_chg:.3f}p</div>' if us10y_chg >= 0 else f'<div class="metric-delta-neg">▼ {abs(us10y_chg):.3f}p</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col5:
            dxy = rf.get("dxy"); dxy_chg = rf.get("dxy_chg")
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">달러 인덱스 (DXY)</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{dxy:.2f}</div>' if dxy is not None else '<div class="metric-value">N/A</div>', unsafe_allow_html=True)
            if dxy_chg is not None:
                st.markdown(f'<div class="metric-delta-pos">↑ {dxy_chg:.2f}%</div>' if dxy_chg >= 0 else f'<div class="metric-delta-neg">↓ {abs(dxy_chg):.2f}%</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col6:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">참고</div>', unsafe_allow_html=True)
            st.markdown('<div class="small-muted">※ 수치는 약간의 지연이 있을 수 있습니다.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        st.caption("📈 ETF 3대장 (QQQ · VOO · SOXX)")
        if etfs:
            cols_etf = st.columns(3)
            for i, e in enumerate(etfs):
                with cols_etf[i]:
                    sym = e.get("symbol")
                    current = e.get("current")
                    chg = e.get("chg_pct")
                    basis = e.get("basis")
                    state = e.get("market_state", "")

                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-label">{sym}</div>', unsafe_allow_html=True)
                    value_str = f"{current:.2f}" if current is not None else "N/A"
                    st.markdown(f'<div class="metric-value">{value_str}</div>', unsafe_allow_html=True)
                    if chg is not None:
                        st.markdown(f'<div class="metric-delta-pos">↑ {chg:.2f}%</div>' if chg >= 0 else f'<div class="metric-delta-neg">↓ {abs(chg):.2f}%</div>', unsafe_allow_html=True)
                    extra = basis + (f" · 상태: {state}" if state else "")
                    st.markdown(f'<div class="small-muted">{extra}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            st.caption("※ %는 전일 종가 대비 기준입니다.")
        else:
            st.write("ETF 데이터를 불러오지 못했습니다.")

        st.markdown("---")

        # 레이어
        bt_score = bigtech_layer.get("score", 0)
        bt_items = bigtech_layer.get("items", [])
        st.markdown('<div class="card-soft">', unsafe_allow_html=True)
        st.markdown('<div class="layer-title-en">BIG TECH LAYER</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chip chip-green">빅테크 강도 점수: {bt_score}</div>', unsafe_allow_html=True)
        for it in bt_items:
            sym = it["symbol"]; chg = it["chg"]
            if chg is None:
                continue
            sign = "+" if chg > 0 else ""
            cls = "layer-chg-pos" if chg > 0 else ("layer-chg-neg" if chg < 0 else "layer-chg-flat")
            st.markdown(f'<div class="layer-row"><span class="layer-symbol">{sym}</span><span class="{cls}">{sign}{chg:.2f}%</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        sec_score = sector_layer.get("score", 0)
        sec_items = sector_layer.get("items", [])
        st.markdown('<div class="card-soft">', unsafe_allow_html=True)
        st.markdown('<div class="layer-title-en">SECTOR ROTATION LAYER</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chip chip-blue">섹터 점수: {sec_score}</div>', unsafe_allow_html=True)
        for it in sec_items:
            label = it["label"]; chg = it["chg"]
            if chg is None:
                continue
            sign = "+" if chg > 0 else ""
            cls = "layer-chg-pos" if chg > 0 else ("layer-chg-neg" if chg < 0 else "layer-chg-flat")
            st.markdown(f'<div class="layer-row"><span class="layer-symbol">{label}</span><span class="{cls}">{sign}{chg:.2f}%</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="small-muted">※ 섹터별 강도 흐름으로 쏠림 체크</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # 2) 내 종목 자동 판독기
    st.subheader("🔍 내 종목 자동 판독기 + 실전 보조지표")

    col_top1, col_top2 = st.columns(2)
    with col_top1:
        user_symbol = st.text_input("종목 이름/티커 (예: NVDA, 엔비디아, META, TQQQ)", key="symbol_input")
        holding_type = st.radio("보유 상태", ["보유 중", "신규 진입 검토"], horizontal=True)

    with col_top2:
        mode_name = st.selectbox("투자 모드 선택", ["단타", "스윙", "장기"], index=1)
        commission_pct = st.number_input("왕복 수수료/비용(%) (기본 0.2% 가정)", min_value=0.0, max_value=2.0, value=0.2, step=0.05)

    cfg = get_mode_config(mode_name)

    # 보유정보
    col_mid1, col_mid2 = st.columns(2)
    avg_price = 0.0
    shares = 0
    if holding_type == "보유 중":
        with col_mid1:
            avg_price = st.number_input("내 평단가 (USD)", min_value=0.0, value=0.0, step=0.01)
        with col_mid2:
            shares = st.number_input("보유 수량 (주)", min_value=0, value=0, step=1)

    # 분석 버튼
    run_click = st.button("🚀 분석하기", key="run_analyze")
    run_from_side = st.session_state.get("run_from_side", False)
    run = run_click or run_from_side
    st.session_state["run_from_side"] = False

    # 신규 진입 스캐너 (번잡함 해결: expander + 결과 저장)
    with st.expander("📊 신규 진입 스캐너 (A안, 간단)", expanded=False):
        scan_click = st.button("🛰 스캐너 실행", key="run_scan")
        if scan_click:
            with st.spinner("신규 진입 후보 종목 스캔 중..."):
                scan_mkt_score, scan_list = scan_new_entry_candidates(cfg)
            st.session_state["scan_results"] = {"market_score": scan_mkt_score, "items": scan_list}

        scan_data = st.session_state.get("scan_results")
        if scan_data:
            scan_mkt_score = scan_data["market_score"]
            scan_list = scan_data["items"]

            if scan_mkt_score <= -4:
                st.warning("시장 점수가 강한 Risk-off 구간 → 신규 진입은 보수적으로")

            if not scan_list:
                st.write("조건을 만족하는 후보가 없습니다.")
            else:
                st.caption(f"총 **{len(scan_list)}개** 종목 후보")
                scan_clicked_symbol = None
                for item in scan_list:
                    sym = item["symbol"]
                    st.markdown(f"**{sym}** | 현재가 **{item['price']:.2f}** | RSI **{item['rsi']:.1f}** | {item['bias']} | 스코어 **{item['score']:.1f}**")
                    if st.button(f"🔍 {sym} 바로 분석", key=f"scan_go_{sym}"):
                        scan_clicked_symbol = sym

                if scan_clicked_symbol:
                    st.session_state["pending_symbol"] = scan_clicked_symbol
                    st.session_state["scroll_to_result"] = True
                    st.rerun()

    if not run:
        st.stop()

    # ====== 분석 시작 ======
    symbol = normalize_symbol(user_symbol)
    if not symbol:
        st.error("❌ 종목 이름 또는 티커가 비어있습니다.")
        st.stop()

    with st.spinner("데이터 불러오는 중..."):
        ov = get_us_market_overview()
        fgi = ov.get("fgi")
        score_mkt, _, _ = compute_market_score(ov)

        df = get_price_data(symbol, cfg["period"])
        if df.empty:
            st.error("❌ 데이터 부족/티커 오류")
            st.stop()

        df = add_indicators(df)
        if df.empty:
            st.error("❌ 지표 계산 데이터 부족")
            st.stop()

        last = df.iloc[-1]
        df_5m = get_intraday_5m(symbol)

    # 최근 검색 저장
    if symbol not in st.session_state["recent_symbols"]:
        st.session_state["recent_symbols"].append(symbol)
        st.session_state["recent_symbols"] = st.session_state["recent_symbols"][-30:]

    # 가격/손익
    price = float(last["Close"])
    profit_pct = (price - avg_price) / avg_price * 100 if avg_price > 0 else 0.0
    total_pnl = (price - avg_price) * shares if (shares > 0 and avg_price > 0) else 0.0

    buy_low, buy_high, tp0, tp1, tp2, sl0, sl1 = calc_levels(df, last, cfg)

    # ✅ 신규 진입 손절은 "매수 가설 실패" 관점으로 별도 조정
    if holding_type == "신규 진입 검토" and buy_low is not None:
        sl0 = buy_low * 0.97
        sl1 = buy_low * 0.94

    bias_comment = short_term_bias(last)
    gap_pct, gap_comment = calc_gap_info(df)
    atr14 = float(last["ATR14"]) if not np.isnan(last["ATR14"]) else None
    intraday_sc, intraday_comment = get_intraday_5m_score(df_5m)
    ext_price = get_last_extended_price(symbol)

    signal = make_signal(last, holding_type, fgi, tp1, sl0)

    # 즐겨찾기
    is_fav = symbol in st.session_state["favorite_symbols"]
    fav_new = st.checkbox("⭐ 이 종목 즐겨찾기", value=is_fav)
    if fav_new and not is_fav:
        st.session_state["favorite_symbols"].append(symbol)
    elif (not fav_new) and is_fav:
        st.session_state["favorite_symbols"].remove(symbol)

    # ✅ 분석 결과로 자동 스크롤 (확실히 동작)
    st.markdown('<div id="analysis_result_anchor"></div>', unsafe_allow_html=True)
    if st.session_state.get("scroll_to_result", True):
        st.markdown(
            """
            <script>
            setTimeout(function () {
                var el = document.getElementById("analysis_result_anchor");
                if (el) { el.scrollIntoView({behavior: "smooth", block: "start"}); }
            }, 250);
            </script>
            """,
            unsafe_allow_html=True,
        )
    st.session_state["scroll_to_result"] = False

    # ==========================
    # UI 출력 (보유/신규 공통으로 항상 뜸)
    # ==========================
    st.subheader("🧾 요약")
    st.write(f"- 입력 종목: **{user_symbol}** → 실제 티커: **{symbol}**")
    st.write(f"- 공포·탐욕지수(FGI): **{fgi:.1f}**" if fgi is not None else "- 공포·탐욕지수(FGI): 조회 실패")
    st.write(f"- 시장 점수: **{score_mkt} / 8**")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("정규장 기준 현재가", f"{price:.2f} USD")
        if ext_price is not None:
            diff_pct = (ext_price - price) / price * 100
            sign = "+" if diff_pct >= 0 else ""
            st.caption(f"시외 포함 최근가: {ext_price:.2f} ({sign}{diff_pct:.2f}%)")

    with col_b:
        st.markdown(
            f"""
            <div class="card-soft-sm">
              <div class="small-muted">MODE</div>
              <div style="font-size:1.05rem;font-weight:600;">{cfg['name']} 모드</div>
              <div class="small-muted">차트 기간: {cfg['period']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_c:
        st.markdown(
            f"""
            <div class="card-soft-sm">
              <div class="small-muted">POSITION</div>
              <div>보유 상태: <b>{holding_type}</b></div>
              <div class="small-muted">보유중이면 평단/손익, 신규면 진입/가설 중심</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if holding_type == "보유 중" and avg_price > 0:
        st.write(f"- 평단가: **{avg_price:.2f} USD**")
        st.write(f"- 수익률: **{profit_pct:.2f}%**")
    if holding_type == "보유 중" and shares > 0 and avg_price > 0:
        rate = get_usdkrw_rate()
        cost_factor = 1 - commission_pct / 100
        total_pnl_after_fee = total_pnl * cost_factor
        pnl_krw = total_pnl_after_fee * rate
        st.write(f"- 평가손익(수수료 {commission_pct:.2f}% 반영): **{total_pnl_after_fee:,.2f} USD** (약 **{pnl_krw:,.0f} KRW**, 환율 {rate:,.2f}원)")

    st.subheader("🎯 매매 판단 (핵심)")
    col_sig1, col_sig2 = st.columns([2, 1])
    with col_sig1:
        st.write(f"**추천 액션:** ⭐ {signal} ⭐")
        st.write(f"**단기 방향성:** {bias_comment}")
    with col_sig2:
        st.caption("※ 신호는 추세/지지·저항/모멘텀 중심이며, 시장 점수는 톤 조절에 사용")

    st.subheader("📌 가격 레벨 (진입/익절/손절 가이드)")
    if buy_low is not None and buy_high is not None:
        st.write(f"- 매수 관심 구간: **{buy_low:.2f} ~ {buy_high:.2f} USD**")
    if tp0 is not None:
        st.write(f"- 0차 매도(부분 익절): **{tp0:.2f} USD**")
    if tp1 is not None:
        st.write(f"- 1차 매도(주요 저항/목표): **{tp1:.2f} USD**")
    if tp2 is not None:
        st.write(f"- 2차 매도(확장 목표): **{tp2:.2f} USD**")
    if sl0 is not None:
        st.write(f"- 0차 손절(추세 이탈선): **{sl0:.2f} USD**")
    if sl1 is not None:
        st.write(f"- 1차 손절(최종 방어선): **{sl1:.2f} USD**")

    st.caption("※ 보유중이면 '방어선(sl) vs 저항(tp)'로 관리, 신규면 '매수 가설 실패(sl)' 기준이 더 중요")

    st.subheader("📊 갭 · 변동성 · 장중 흐름")
    col_gap, col_atr, col_intra = st.columns(3)
    with col_gap:
        if gap_pct is not None:
            st.metric("전일 대비 갭(시가 기준)", f"{gap_pct:.2f}%")
            st.caption(gap_comment)
        else:
            st.caption("갭 정보 부족")
    with col_atr:
        if atr14 is not None:
            st.metric("ATR(14, 일봉)", f"{atr14:.2f}")
        else:
            st.caption("ATR 계산 불가")
    with col_intra:
        if intraday_sc is not None:
            st.metric("장중 흐름 스코어 (0~4)", f"{intraday_sc}")
            st.caption(intraday_comment)
        else:
            st.caption(intraday_comment)

    # =====================================
    # ✅ AI 자동분석 (요청한 5가지 기능)
    # - 문구: "AI 자동분석" (gpt 단어 제거)
    # =====================================
    st.markdown("---")
    st.subheader("🤖 AI 자동분석")
    st.caption("※ 버튼을 눌렀을 때만 AI를 호출합니다. (비용/속도 관리)")

    use_ai = st.toggle("AI 자동분석 사용", value=False)
    ai_run = st.button("🧠 AI 자동분석 실행", disabled=not use_ai)

    if use_ai and ai_run:
        levels = {
            "buy_low": None if buy_low is None else float(buy_low),
            "buy_high": None if buy_high is None else float(buy_high),
            "tp0": None if tp0 is None else float(tp0),
            "tp1": None if tp1 is None else float(tp1),
            "tp2": None if tp2 is None else float(tp2),
            "sl0": None if sl0 is None else float(sl0),
            "sl1": None if sl1 is None else float(sl1),
        }
        indicators = {
            "rsi": float(last["RSI14"]),
            "macd": float(last["MACD"]),
            "macds": float(last["MACD_SIGNAL"]),
            "ma20": float(last["MA20"]),
            "ma50": float(last["MA50"]),
            "atr14": float(last["ATR14"]) if not np.isnan(last["ATR14"]) else None,
            "k": float(last["STOCH_K"]),
            "d": float(last["STOCH_D"]),
        }

        with st.spinner("AI 자동분석 생성 중..."):
            ai_data, ai_err = call_ai_auto_analysis(
                symbol=symbol,
                holding_type=holding_type,
                mode_name=cfg["name"],
                market_score=score_mkt,
                fgi=(None if fgi is None else float(fgi)),
                price=price,
                levels=levels,
                indicators=indicators,
                signal=signal,
                bias_comment=bias_comment,
            )

        if ai_err:
            st.error(ai_err)
        else:
            # 1) 한 줄 결론
            st.markdown("### 1️⃣ 한 줄 결론")
            st.success(ai_data.get("one_line", ""))

            # 2) 헷갈리는 구간 설명
            st.markdown("### 2️⃣ 헷갈리는 구간 설명")
            st.write(ai_data.get("confusing_zone", ""))

            # 3) IF-THEN 행동 카드
            st.markdown("### 3️⃣ IF-THEN 행동 카드")
            cards = ai_data.get("if_then_cards", [])
            if not cards:
                st.caption("카드가 비어있습니다.")
            else:
                for c in cards[:5]:
                    st.markdown(
                        f"""
                        <div class="card-soft">
                          <div class="small-muted">IF</div>
                          <div style="font-size:1.05rem;font-weight:700;">{c.get('if','')}</div>
                          <div class="small-muted" style="margin-top:8px;">THEN</div>
                          <div style="font-size:1.0rem;font-weight:600;">{c.get('then','')}</div>
                          <div class="small-muted" style="margin-top:8px;">NOTE</div>
                          <div>{c.get('note','')}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            # 4) 시장 톤 조절
            st.markdown("### 4️⃣ 시장 톤 조절")
            st.info(ai_data.get("market_tone", ""))

            # 5) 질문형 판독
            st.markdown("### 5️⃣ 질문형 판독")
            qs = ai_data.get("questions", [])
            if qs:
                for q in qs[:3]:
                    st.write("- " + str(q))

            st.markdown("### ✅ 안전장치(Guardrails)")
            gr = ai_data.get("guardrails", [])
            if gr:
                for g in gr[:4]:
                    st.write("- " + str(g))

            with st.expander("AI 원본 JSON 보기", expanded=False):
                st.json(ai_data)

    # =====================================
    # 차트 (간단 버전: 확대/드래그 거의 없음)
    # =====================================
    st.subheader("📈 가격 / 볼린저밴드 차트 (최근)")
    chart_df = df[["Close", "MA20", "BBL", "BBU"]].tail(120)
    st.line_chart(chart_df)
