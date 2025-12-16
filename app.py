import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests

# 선택 기능: AI 해석(요약/헷갈림 설명)
try:
    from openai import OpenAI
except Exception:
    OpenAI = None
import os
import json
import re
import hashlib


# =====================================
# 페이지 설정
# =====================================
st.set_page_config(
    page_title="내 주식 자동판독기 (시장 개요 + 레이어/갭/ATR/장중 흐름)",
    page_icon="📈",
    layout="wide",
)

# =====================================
# 전체 스타일 (라이트 + 모바일 가독성 강화)
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

[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #f4f7ff 0%, #eefdfd 50%, #fdfcfb 100%);
}

main.block-container {
    max-width: 1250px;
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}

header, [data-testid="stHeader"], [data-testid="stSidebar"] {
    background-color: #ffffff !important;
}

[data-testid="stExpander"],
[data-testid="stExpander"] > details,
[data-testid="stExpander"] details > summary,
[data-testid="stExpander"] details > div {
    background-color: #ffffff !important;
    color: #111827 !important;
}

/* 제목들 */
h1 { font-size: 1.6rem; font-weight: 700; color: #111827 !important; }
h2 { font-size: 1.25rem; font-weight: 600; color: #111827 !important; }
h3 { font-size: 1.05rem; font-weight: 600; color: #111827 !important; }

/* 기본 텍스트 */
p, label, span, div { font-size: 0.94rem; color: #111827 !important; }

.small-muted { font-size: 0.8rem; color: #6b7280 !important; }

/* 공통 카드 */
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

/* 레이어 */
.layer-title-en {
    font-size: 0.85rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #6b7280 !important;
    margin-bottom: 4px;
}
.layer-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 4px;
}
.layer-symbol { font-weight: 600; font-size: 0.95rem; color: #111827 !important; }
.layer-chg-pos { font-weight: 600; font-size: 0.95rem; color: #dc2626 !important; } /* 빨강 */
.layer-chg-neg { font-weight: 600; font-size: 0.95rem; color: #2563eb !important; } /* 파랑 */
.layer-chg-flat{ font-weight: 600; font-size: 0.95rem; color: #4b5563 !important; }

/* metric 카드 */
.metric-card {
    background: rgba(255, 255, 255, 0.96);
    border-radius: 20px;
    padding: 12px 16px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
    margin-bottom: 8px;
}
.metric-label { font-size: 0.8rem; font-weight: 500; color: #6b7280 !important; }
.metric-value { font-size: 1.3rem; font-weight: 700; margin-top: 4px; color: #111827 !important; }
.metric-delta-pos {
    display: inline-flex; align-items: center;
    margin-top: 6px; padding: 2px 8px; border-radius: 999px;
    background: #bbf7d0; color: #166534 !important;
    font-size: 0.78rem; font-weight: 600;
}
.metric-delta-neg {
    display: inline-flex; align-items: center;
    margin-top: 6px; padding: 2px 8px; border-radius: 999px;
    background: #fee2e2; color: #b91c1c !important;
    font-size: 0.78rem; font-weight: 600;
}

/* 입력 박스 */
[data-baseweb="input"] > div,
[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    border-radius: 999px !important;
    border: 1px solid #e5e7eb !important;
}
[data-baseweb="input"] input, textarea { background-color: transparent !important; color: #111827 !important; }
textarea { border-radius: 16px !important; }
input::placeholder, textarea::placeholder { color: #9ca3af !important; }

[data-baseweb="radio"] > label { background-color: transparent !important; color: #111827 !important; }
button[role="tab"] > div { color: #111827 !important; }

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

[data-testid="stDataFrame"], [data-testid="stTable"] { background-color: #ffffff; }

@media (max-width: 768px) {
    .metric-value { font-size: 1.4rem; }
    .layer-symbol, .layer-chg-pos, .layer-chg-neg, .layer-chg-flat { font-size: 1.0rem; }
}

[data-testid="stExpander"] summary { color: #111827 !important; }
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
    "엔페이즈": "ENPH",
    "코카콜라": "KO", "펩시": "PEP",
    "맥도날드": "MCD", "스타벅스": "SBUX",
    "나이키": "NKE", "월마트": "WMT", "코스트코": "COST",
    "존슨앤존슨": "JNJ", "존슨앤드존슨": "JNJ",
    "화이자": "PFE", "모더나": "MRNA",
    "유나이티드헬스": "UNH", "메르크": "MRK", "애브비": "ABBV",
    "JP모건": "JPM", "제이피모건": "JPM",
    "골드만삭스": "GS", "모건스탠리": "MS",
    "뱅크오브아메리카": "BAC",
    "씨티": "C", "씨티그룹": "C",
    "페이팔": "PYPL",
    "엑슨모빌": "XOM", "셰브론": "CVX",
    "캐터필러": "CAT", "3M": "MMM",
    "허니웰": "HON", "디즈니": "DIS",
    "버라이즌": "VZ", "AT&T": "T",
    "오라클": "ORCL",
    "코인베이스": "COIN", "코인베이스글로벌": "COIN",
    "마이크로스트래티지": "MSTR",
    "리오트": "RIOT", "라이엇": "RIOT",
    "마라톤디지털": "MARA", "마라톤": "MARA",
    "클린스파크": "CLSK",
    "비트팜": "BITF",
    "갤럭시디지털": "BRPHF",
    "QQQ": "QQQ", "나스닥ETF": "QQQ", "나스닥100": "QQQ",
    "SPY": "SPY", "S&P500": "SPY", "SP500": "SPY",
    "VOO": "VOO", "S&P인덱스": "VOO",
    "SOXL": "SOXL", "반도체3배": "SOXL",
    "SOXS": "SOXS", "반도체인버스3배": "SOXS",
    "TQQQ": "TQQQ", "나스닥3배": "TQQQ",
    "SQQQ": "SQQQ", "나스닥인버스3배": "SQQQ",
    "TECL": "TECL", "기술주3배": "TECL",
    "SPXL": "SPXL", "S&P3배": "SPXL",
    "SPXS": "SPXS", "S&P인버스3배": "SPXS",
    "LABU": "LABU", "바이오3배": "LABU",
    "LABD": "LABD", "바이오인버스3배": "LABD",
    "ARKK": "ARKK",
    "비트코인ETF": "IBIT",
    "아이쉐어즈비트코인": "IBIT",
}

POPULAR_SYMBOLS = [
    "NVDA", "META", "TSLA", "AAPL", "MSFT", "AMZN",
    "QQQ", "TQQQ", "SOXL", "SPY", "VOO",
    "COIN", "MSTR", "RIOT", "MARA",
    "ORCL", "PYPL", "NFLX", "PLTR", "AVGO",
]

SCAN_CANDIDATES = sorted(set(
    POPULAR_SYMBOLS + ["NVDA", "AAPL", "MSFT", "AMZN", "META", "GOOGL", "TSLA"]
))

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
        return {
            "symbol": symbol,
            "name": name,
            "current": None,
            "basis": "조회 실패",
            "chg_pct": None,
            "market_state": "",
        }

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

    # [추가] 지수(확정)용: 나스닥/ S&P 지수 변화(정규장 기준)
    ixic_last, ixic_chg, ixic_state = safe_last_change_info("^IXIC")
    gspc_last, gspc_chg, gspc_state = safe_last_change_info("^GSPC")
    overview["indexes"] = {
        "nasdaq": {"last": ixic_last, "chg_pct": ixic_chg, "state": ixic_state},
        "sp500": {"last": gspc_last, "chg_pct": gspc_chg, "state": gspc_state},
    }

    etfs = [
        get_etf_price_with_prepost("QQQ", "QQQ (나스닥100 ETF)"),
        get_etf_price_with_prepost("VOO", "VOO (S&P500 ETF)"),
        get_etf_price_with_prepost("SOXX", "SOXX (반도체 ETF)"),
    ]
    overview["etfs"] = etfs

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

# =========================================================
# [추가] 시장 판독 한 줄 결론(점수 → 문구 고정) + 장 상태 배지
# =========================================================
def _clamp(x, lo=0.0, hi=100.0):
    try:
        x = float(x)
    except Exception:
        return lo
    return max(lo, min(hi, x))

def score_to_text(score_0_100: float) -> str:
    s = float(score_0_100)
    if s >= 70:
        return "위험선호 우세"
    elif s >= 65:
        return "양호"
    elif s >= 52:
        return "반등 시도"
    elif s >= 45:
        return "추세 불안"
    else:
        return "위험회피 우세"

def market_state_badge_from_etfs(etfs: list):
    # ETF 3대장 중 상태가 있는 걸 우선 사용(대부분 QQQ가 잡힘)
    stt = ""
    if etfs:
        for e in etfs:
            ms = (e.get("market_state") or "").strip()
            if ms:
                stt = ms
                break

    # yfinance marketState 예: PRE / REGULAR / POST / CLOSED 등
    if stt == "PRE":
        return "🟡 프리장", "chip chip-blue"
    if stt == "POST":
        return "🟣 애프터장", "chip chip-blue"
    if stt == "REGULAR":
        return "🟢 정규장", "chip chip-green"

    # 애매한 경우(빈 값/기타)
    if stt:
        return f"⚪ 장 상태: {stt}", "chip chip-blue"
    return "⚪ 장 상태: 확인중", "chip chip-blue"

def compute_market_verdict_scores(overview: dict):
    """
    반환:
      macro_0_100 : 세계지표(=Risk-on/off 종합 점수) (compute_market_score 기반)
      etf_0_100   : ETF 선행(프리/정규/애프터 포함)
      index_0_100 : 지수(정규장 확정) (^IXIC, ^GSPC 기반)
      leader_0_100: 빅테크 리더십 (BIGTECH 점수 기반)
      conclusion  : 신규진입 결론
      holder_line : 보유자 대응 한 줄
      lines       : 판독 4줄(문구 고정)
    """
    if not overview:
        return None

    # 1) macro: 기존 compute_market_score(-8~8)를 0~100으로 맵핑
    mkt_score, _, _ = compute_market_score(overview)
    macro_0_100 = _clamp((mkt_score + 8) / 16 * 100)

    # 2) ETF 선행: ETF 3대장 평균 변화율(전일종가 대비)을 0~100으로 맵핑
    etfs = overview.get("etfs", []) or []
    etf_chgs = [e.get("chg_pct") for e in etfs if e.get("chg_pct") is not None]
    if etf_chgs:
        avg_etf = float(np.mean(etf_chgs))
        # +1%면 70, -1%면 30 정도가 되도록 스케일 (경험적)
        etf_0_100 = _clamp(50 + avg_etf * 20)
    else:
        etf_0_100 = 50.0

    # 3) Index 확정: ^IXIC / ^GSPC 변화율 평균으로 0~100 맵핑
    idx = overview.get("indexes", {}) or {}
    ixic = idx.get("nasdaq", {}) or {}
    gspc = idx.get("sp500", {}) or {}
    idx_chgs = [v for v in [ixic.get("chg_pct"), gspc.get("chg_pct")] if v is not None]
    if idx_chgs:
        avg_idx = float(np.mean(idx_chgs))
        index_0_100 = _clamp(50 + avg_idx * 20)
    else:
        # 데이터가 없으면 선물로 대체(보수적)
        fut = overview.get("futures", {}) or {}
        nas_f = (fut.get("nasdaq", {}) or {}).get("chg_pct")
        if nas_f is not None:
            index_0_100 = _clamp(50 + float(nas_f) * 18)
        else:
            index_0_100 = 50.0

    # 4) Leader: bigtech score(-7~+7)를 0~100으로 맵핑
    bt = overview.get("bigtech", {}) or {}
    bt_score = bt.get("score", 0)
    n = max(1, len(BIGTECH_LIST))
    leader_0_100 = _clamp(50 + (float(bt_score) / n) * 30)

    # 문구(고정)
    line_macro = f"세계지표: {score_to_text(macro_0_100)}"
    # ETF는 항상 “선행(확인필요)” 느낌을 주기 위해 괄호로만 고정
    etf_text = score_to_text(etf_0_100)
    if etf_0_100 >= 65:
        etf_text = f"{etf_text} (정규장 확인 필요)"
    elif etf_0_100 < 50:
        etf_text = f"{etf_text} (리스크 경계)"
    else:
        etf_text = f"{etf_text} (대기)"

    line_etf = f"ETF 선행: {etf_text}"

    idx_text = score_to_text(index_0_100)
    # 지수는 “반등 시도 중이나 추세 불안” 같은 조합을 더 자주 쓰게 보정
    if 52 <= index_0_100 < 60:
        idx_text = "반등 시도 중이나 추세 불안"
    elif 45 <= index_0_100 < 52:
        idx_text = "추세 불안"
    line_index = f"지수 점수: {idx_text}"

    leader_text = score_to_text(leader_0_100)
    # 빅테크는 “상단 부담”을 중간 구간 문구로 고정
    if 58 <= leader_0_100 < 68:
        leader_text = "상단 부담"
    elif 52 <= leader_0_100 < 58:
        leader_text = "힘 부족"
    elif leader_0_100 < 52:
        leader_text = "주도력 상실"
    elif leader_0_100 >= 68:
        leader_text = "주도력 확실"
    line_leader = f"빅테크: {leader_text}"

    # 결론(if/score) — 네가 원한 “2줄 결론” 고정
    # 컷라인(우리가 합의한 실전용)
    if macro_0_100 < 45:
        conclusion = "신규진입 불리"
        holder_line = "보유자는 방어적 대응"
    elif (index_0_100 < 52) or (leader_0_100 < 52):
        conclusion = "신규진입 신중"
        holder_line = "보유자는 단기 반등까지만 대응"
    elif (macro_0_100 >= 60) and (index_0_100 >= 60) and (leader_0_100 >= 58):
        conclusion = "신규진입 가능"
        holder_line = "보유자는 추세 추종 가능"
    else:
        conclusion = "선별적 접근"
        holder_line = "보유자는 분할 대응"

    return {
        "macro": macro_0_100,
        "etf": etf_0_100,
        "index": index_0_100,
        "leader": leader_0_100,
        "lines": [line_macro, line_etf, line_index, line_leader],
        "conclusion": conclusion,
        "holder_line": holder_line,
    }

# =====================================
# 가격 데이터 + 지표
# =====================================
def get_price_data(symbol, period="6mo"):
    if not symbol or symbol.strip() == "":
        return pd.DataFrame()
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval="1d", auto_adjust=False)
    except ValueError:
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
    df["STOCH_K"] = (close - low14) / (high14 - low14) * 100
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
# AI 해석(요약/헷갈림 설명) 유틸
# =====================================
def _ai_make_cache_key(symbol: str, holding_type: str, mode_name: str, avg_price: float, df_last: pd.Series, market_label: str):
    payload = {
        "symbol": symbol,
        "holding_type": holding_type,
        "mode": mode_name,
        "avg_price": round(float(avg_price or 0.0), 4),
        "close": round(float(df_last.get("Close", 0.0)), 4),
        "ma20": round(float(df_last.get("MA20", 0.0)), 4),
        "bbl": round(float(df_last.get("BBL", 0.0)), 4),
        "bbu": round(float(df_last.get("BBU", 0.0)), 4),
        "rsi": round(float(df_last.get("RSI14", 0.0)), 4),
        "macd": round(float(df_last.get("MACD", 0.0)), 4),
        "macds": round(float(df_last.get("MACD_SIGNAL", 0.0)), 4),
        "market": market_label,
    }
    s = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def _ai_extract_json(text: str):
    if not text:
        return None
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None

def ai_summarize_and_explain(
    symbol: str,
    holding_type: str,
    mode_name: str,
    market_label: str,
    market_detail: str,
    price: float,
    avg_price: float,
    signal: str,
    bias_comment: str,
    gap_comment: str,
    rr: float,
    levels: dict,
    last_row: pd.Series,
    extra_notes: list,
    model_name: str = "gpt-4o-mini",
):
    if OpenAI is None:
        return None, "openai 패키지를 찾지 못했습니다. requirements.txt에 openai를 추가했는지 확인하세요."
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None, "OPENAI_API_KEY 환경변수가 비어 있습니다. Streamlit Cloud → Settings → Secrets에 설정하세요."

    client = OpenAI(api_key=api_key)

    compact = {
        "symbol": symbol,
        "holding_type": holding_type,
        "mode": mode_name,
        "market": {"label": market_label, "detail": market_detail},
        "price": price,
        "avg_price": avg_price,
        "signal": signal,
        "bias": bias_comment,
        "gap": gap_comment,
        "rr_ratio": rr,
        "levels": levels,
        "indicators": {
            "MA20": float(last_row["MA20"]),
            "BBL": float(last_row["BBL"]),
            "BBU": float(last_row["BBU"]),
            "RSI14": float(last_row["RSI14"]),
            "MACD": float(last_row["MACD"]),
            "MACD_SIGNAL": float(last_row["MACD_SIGNAL"]),
            "STOCH_K": float(last_row["STOCH_K"]),
            "STOCH_D": float(last_row["STOCH_D"]),
            "ATR14": float(last_row["ATR14"]),
        },
        "notes": extra_notes[:8],
    }

    system = (
        "너는 '주식 자동판독기'의 해석 도우미다. "
        "확정 매수/매도 지시를 하지 말고, "
        "지표가 말하는 바를 짧고 명확하게 정리한다. "
        "모호하면 모호하다고 말한다. "
        "반드시 JSON만 출력한다."
    )

    if holding_type == "보유 중":
        confusion_title_2 = "보유자 관점: 왜 버티기/비중조절이 애매한가"
        confusion_focus_2 = "평단·손절선(sl0/sl1)·목표가(tp1) 기준으로 '지금 유지/축소가 왜 애매한지'를 설명"
    else:
        confusion_title_2 = "신규 진입 관점: 왜 지금 바로 들어가기 애매한가"
        confusion_focus_2 = "진입 밴드(buy_low~buy_high)·손절선(sl0)·확인 신호(추세/모멘텀) 기준으로 '왜 대기/확인이 필요한지'를 설명"

    user = (
        "아래 데이터는 기술적 지표 기반의 요약 데이터다.\n"
        "반드시 아래 JSON 형태로만 출력해라(키/구조/타입 고정).\n\n"
        "{\n"
        "  \"summary_one_line\": \"가격 위치(MA20/BB 중 1개 이상) + 모멘텀(RSI/MACD 중 1개 이상) + 행동 해석(관망/유지/축소/대기 등)을 모두 포함한 한 문장\",\n"
        "  \"confusion_explain\": [\n"
        "    {\n"
        "      \"title\": \"왜 지금 이 신호가 나왔나\",\n"
        "      \"desc\": \"반드시 MA20/BBL/BBU/RSI/MACD/ATR 중 최소 2개 이상을 직접 언급하고, buy_low~buy_high 또는 tp/sl 같은 레벨을 최소 1개 언급해 구체적으로 설명\"\n"
        "    },\n"
        "    {\n"
        f"      \"title\": \"{confusion_title_2}\",\n"
        f"      \"desc\": \"{confusion_focus_2}. 반드시 수치/레벨(평단 또는 buy_band/tp/sl)을 1개 이상 언급\"\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        "제약:\n"
        "- 추상적인 문장(\"애매함\", \"모호함\"만)으로 끝내지 마라.\n"
        "- 확정 매수/매도 지시는 금지(\"지금 사라/팔아라\" 금지).\n"
        "- JSON 외 텍스트 출력 금지.\n\n"
        f"DATA:\n{json.dumps(compact, ensure_ascii=False)}"
    )

    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.2,
        )
        text = (resp.choices[0].message.content or "").strip()
        parsed = _ai_extract_json(text)
        if parsed and isinstance(parsed.get("summary_one_line"), str) and isinstance(parsed.get("confusion_explain"), list):
            if len(parsed["confusion_explain"]) >= 2:
                return parsed, None
            return None, "AI 응답이 너무 짧습니다(헷갈림 설명 블록 부족)."
        return None, "AI 응답에서 JSON 파싱 실패 (모델이 형식을 어겼습니다)."
    except Exception as e:
        return None, f"AI 호출 실패: {e}"

def request_ai_generation():
    st.session_state["ai_request"] = True
    st.session_state["scroll_to_result"] = True


# =====================================
# 코멘트/판단 함수들
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

    if rsi > 60: score += 1
    elif rsi < 40: score -= 1

    if k > d and k > 50: score += 1
    elif k < d and k < 50: score -= 1

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

    tp1 = price * 1.08 if base_res <= price else base_res
    tp0 = price + (tp1 - price) * 0.6
    tp2 = tp1 + (tp1 - price) * 0.7

    if rsi > 70:
        tp0 = price + (tp1 - price) * 0.5
        tp2 = tp1 + (tp1 - price) * 0.4

    return tp0, tp1, tp2

def make_signal(row, avg_price, cfg, fgi=None, main_tp=None, main_sl=None):
    price = float(row["Close"])
    bbl = float(row["BBL"])
    bbu = float(row["BBU"])
    ma20 = float(row["MA20"])
    k = float(row["STOCH_K"])
    d = float(row["STOCH_D"])
    macd = float(row["MACD"])
    macds = float(row["MACD_SIGNAL"])
    rsi = float(row["RSI14"])

    fear = (fgi is not None and fgi <= 25)
    greed = (fgi is not None and fgi >= 75)

    strong_overbought = (price > bbu and k > 80 and rsi > 65 and macd < macds)
    mild_overbought = (price > ma20 and (k > 70 or rsi > 60))
    strong_oversold = (price < bbl and k < 20 and d < 20 and rsi < 35)

    if avg_price <= 0:
        if fear and price < bbl * 1.02 and k < 30 and rsi < 45:
            return "초기 매수 관심 (공포 국면)"
        elif greed and price < bbl * 0.98 and k < 15 and rsi < 30:
            return "초기 매수 관심 (탐욕 중 저점)"
        elif strong_oversold:
            return "초기 매수 관심"
        else:
            return "관망 (신규 진입 관점)"

    trend_up = (price > ma20 and macd > macds and rsi >= 45)
    broken_trend = (main_sl is not None and price < main_sl * 0.995)
    near_tp_zone = (main_tp is not None and price >= main_tp * 0.95)

    if broken_trend:
        return "손절 or 비중축소 (주요 지지/추세 이탈)"

    if main_tp is not None and price >= main_tp * 0.98 and strong_overbought:
        return "강한 부분매도 (수익 구간 + 추세 과열)"
    if near_tp_zone and (mild_overbought or rsi > 70):
        return "부분매도 (저항 부근 접근)"

    if strong_oversold and not broken_trend:
        return "합리적 분할매수 (추세 유지 + 과매도)"

    if trend_up:
        return "보유/추세 유지 (상방 추세 진행 중)"

    return "관망 (부분청산·분할매수 모두 애매한 구간)"

def calc_levels(df, last, cfg):
    if df.empty:
        return None, None, None, None, None, None, None

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

def calc_rr_ratio(price, tp, sl):
    if tp is None or sl is None:
        return None
    if tp <= price or sl >= price:
        return None
    risk = price - sl
    reward = tp - price
    if risk <= 0 or reward <= 0:
        return None
    return reward / risk

def get_volume_profile(df: pd.DataFrame, bins: int = 5):
    recent = df.tail(20)
    prices = recent["Close"]
    vols = recent["Volume"]
    if len(recent) < 5:
        return []
    min_p, max_p = prices.min(), prices.max()
    if min_p == max_p:
        return []
    edges = np.linspace(min_p, max_p, bins + 1)
    idx = np.digitize(prices, edges) - 1
    idx = np.clip(idx, 0, bins - 1)
    bucket_vol = {}
    for i, v in zip(idx, vols):
        bucket_vol[i] = bucket_vol.get(i, 0) + v
    levels = []
    for i, total_v in bucket_vol.items():
        low = edges[i]
        high = edges[i + 1]
        mid = (low + high) / 2
        levels.append({"mid": mid, "low": low, "high": high, "volume": total_v})
    return sorted(levels, key=lambda x: x["volume"], reverse=True)[:3]

def get_heavy_days(df: pd.DataFrame, n: int = 3):
    recent = df.tail(30)
    if recent.empty:
        return []
    heavy = recent.sort_values("Volume", ascending=False).head(n)
    res = []
    for idx, row in heavy.iterrows():
        res.append({"date": idx.date(), "close": float(row["Close"]), "volume": int(row["Volume"])})
    return res

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
        score += 1; details.append("5분봉 기준 단기 상방 유지")
    else:
        details.append("5분봉 기준 단기 하락/조정")

    last10 = df_5m.tail(10)
    up_cnt = (last10["Close"] > last10["Open"]).sum()
    if up_cnt >= 6:
        score += 1; details.append(f"최근 10개 캔들 중 {up_cnt}개 상승 (매수 우위)")
    else:
        details.append(f"최근 10개 캔들 중 상승 {up_cnt}개")

    vol_recent = last50["Volume"]
    med_vol = vol_recent.median()
    today_vol = last["Volume"]
    if med_vol > 0 and today_vol > med_vol * 1.3:
        score += 1; details.append("최근 대비 5분봉 거래량 급증")
    else:
        details.append("5분봉 거래량 평이")

    if len(df_5m) >= 2:
        prev = df_5m.iloc[-2]
        if price > prev["Close"]:
            score += 1; details.append("직전 봉 대비 가격 상승")
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

def build_risk_alerts(market_score, last_row, gap_pct, atr14, price_move_abs):
    alerts = []
    if market_score <= -4:
        alerts.append("📉 시장 자체가 강한 Risk-off (지수/금리/달러 조합상 공포장 가능성)")

    rsi = float(last_row["RSI14"])
    if rsi >= 75:
        alerts.append("🔥 RSI 75 이상 – 단기 과열, 급락 조심")
    elif rsi <= 25:
        alerts.append("❄ RSI 25 이하 – 과매도이나 추세 하락일 수 있음")

    if gap_pct is not None and abs(gap_pct) >= 2.0:
        alerts.append(f"⚡ 전일 종가 대비 {gap_pct:.2f}% 갭 – 갭 메움/추세 연장 모두 가능, 변동성 주의")

    if atr14 is not None and atr14 > 0 and price_move_abs is not None:
        atr_ratio = price_move_abs / atr14
        if atr_ratio >= 1.5:
            alerts.append(f"🚨 오늘 움직임이 ATR의 {atr_ratio:.1f}배 – 평소보다 크게 흔들리는 장세")

    if not alerts:
        alerts.append("✅ 특별한 리스크 경고 없음 (기본적인 기술적/시장 환경)")
    return alerts

# =====================================
# 신규 진입 스캐너 (A안: 심플)
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
        if buy_low is None or buy_high is None or tp1 is None:
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

        sl0_new = buy_low * 0.97
        rr = calc_rr_ratio(price, tp1, sl0_new)

        results.append({
            "symbol": sym,
            "price": price,
            "rsi": rsi,
            "bias": bias,
            "dist_band": dist_band_pct,
            "buy_low": buy_low,
            "buy_high": buy_high,
            "tp1": tp1,
            "sl0": sl0_new,
            "rr": rr,
            "score": score,
        })

    results_sorted = sorted(results, key=lambda x: x["score"], reverse=True)
    return market_score, results_sorted[:max_results]

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

if "show_result" not in st.session_state:
    st.session_state["show_result"] = False
if "analysis_params" not in st.session_state:
    st.session_state["analysis_params"] = None
if "ai_cache" not in st.session_state:
    st.session_state["ai_cache"] = {}
if "ai_request" not in st.session_state:
    st.session_state["ai_request"] = False

if st.session_state.get("pending_symbol"):
    ps = st.session_state["pending_symbol"]
    st.session_state["symbol_input"] = ps
    st.session_state["selected_symbol"] = ps
    st.session_state["run_from_side"] = True
    st.session_state["pending_symbol"] = ""

# =====================================
# 레이아웃: 메인 + 사이드
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
    st.caption("시장 개요 + 개별 종목 판독 + 레이어/갭/ATR/장중 흐름을 한 화면에서 확인")

    # 1) 미국 시장 개요 + 레이어
    with st.expander("🌍 미국 시장 실시간 흐름 (보조지표 + 레이어)", expanded=True):
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            refresh = st.button("🔄 새로고침", key="refresh_overview")
        if refresh:
            get_us_market_overview.clear()

        with st.spinner("미국 선물 · 금리 · 달러 · ETF · 레이어 상황 불러오는 중..."):
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
            last = nas.get("last")
            chg = nas.get("chg_pct")
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">나스닥 선물</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{last:.1f}</div>' if last is not None else '<div class="metric-value">N/A</div>', unsafe_allow_html=True)
            if chg is not None:
                st.markdown(f'<div class="metric-delta-pos">↑ {chg:.2f}%</div>' if chg >= 0 else f'<div class="metric-delta-neg">↓ {abs(chg):.2f}%</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            last = es.get("last")
            chg = es.get("chg_pct")
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

        # [추가] 장 상태 배지 + 시장 판독 한 줄 결론(점수→문구 고정)
        verdict = compute_market_verdict_scores(ov)
        session_badge, session_cls = market_state_badge_from_etfs(etfs)

        if verdict:
            st.markdown(
                f"""
                <div class="card-soft">
                  <div class="layer-title-en">MARKET VERDICT</div>
                  <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin-bottom:8px;">
                    <span class="{session_cls}">{session_badge}</span>
                    <span class="chip chip-blue">Macro {verdict['macro']:.0f}</span>
                    <span class="chip chip-blue">ETF {verdict['etf']:.0f}</span>
                    <span class="chip chip-blue">Index {verdict['index']:.0f}</span>
                    <span class="chip chip-blue">BigTech {verdict['leader']:.0f}</span>
                  </div>

                  <div style="line-height:1.55;">
                    <div>🔍 현재 시장 판독</div>
                    <div class="small-muted" style="margin-top:6px;">
                      • {verdict['lines'][0]}<br/>
                      • {verdict['lines'][1]}<br/>
                      • {verdict['lines'][2]}<br/>
                      • {verdict['lines'][3]}
                    </div>
                  </div>

                  <div style="margin-top:10px;">
                    <div style="font-weight:700;">📌 결론</div>
                    <div style="margin-top:4px;">
                      → {verdict['conclusion']}<br/>
                      → {verdict['holder_line']}
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if detail_mkt:
            st.caption("· " + detail_mkt)

        st.markdown("---")

        col4, col5, col6 = st.columns(3)
        with col4:
            us10y = rf.get("us10y")
            us10y_chg = rf.get("us10y_chg")
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">미 10년물</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{us10y:.2f}%</div>' if us10y is not None else '<div class="metric-value">N/A</div>', unsafe_allow_html=True)
            if us10y_chg is not None:
                st.markdown(f'<div class="metric-delta-pos">▲ {us10y_chg:.3f}p</div>' if us10y_chg >= 0 else f'<div class="metric-delta-neg">▼ {abs(us10y_chg):.3f}p</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col5:
            dxy = rf.get("dxy")
            dxy_chg = rf.get("dxy_chg")
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

        # BIG TECH LAYER
        bt_score = bigtech_layer.get("score", 0)
        bt_items = bigtech_layer.get("items", [])
        st.markdown('<div class="card-soft">', unsafe_allow_html=True)
        st.markdown('<div class="layer-title-en">BIG TECH LAYER</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chip chip-green">빅테크 강도 점수: {bt_score}</div>', unsafe_allow_html=True)
        for it in bt_items:
            sym = it["symbol"]
            chg = it["chg"]
            if chg is None:
                continue
            sign = "+" if chg > 0 else ""
            cls = "layer-chg-pos" if chg > 0 else ("layer-chg-neg" if chg < 0 else "layer-chg-flat")
            st.markdown(
                f'<div class="layer-row"><span class="layer-symbol">{sym}</span>'
                f'<span class="{cls}">{sign}{chg:.2f}%</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

        # SECTOR ROTATION LAYER
        sec_score = sector_layer.get("score", 0)
        sec_items = sector_layer.get("items", [])
        st.markdown('<div class="card-soft">', unsafe_allow_html=True)
        st.markdown('<div class="layer-title-en">SECTOR ROTATION LAYER</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chip chip-blue">섹터 점수: {sec_score}</div>', unsafe_allow_html=True)
        for it in sec_items:
            label = it["label"]
            chg = it["chg"]
            if chg is None:
                continue
            sign = "+" if chg > 0 else ""
            cls = "layer-chg-pos" if chg > 0 else ("layer-chg-neg" if chg < 0 else "layer-chg-flat")
            st.markdown(
                f'<div class="layer-row"><span class="layer-symbol">{label}</span>'
                f'<span class="{cls}">{sign}{chg:.2f}%</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown('<div class="small-muted">※ 섹터별 강도 흐름을 통해 쏠림을 한 눈에 체크.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # 2) 내 종목 자동 판독기
    st.subheader("🔍 내 종목 자동 판독기 + 실전 보조지표")

    col_top1, col_top2 = st.columns(2)
    with col_top1:
        user_symbol = st.text_input(
            "종목 이름/티커 (예: NVDA, 엔비디아, META, TQQQ)",
            key="symbol_input",
        )
        holding_type = st.radio("보유 상태", ["보유 중", "신규 진입 검토"], horizontal=True)

    with col_top2:
        mode_name = st.selectbox("투자 모드 선택", ["단타", "스윙", "장기"], index=1)
        commission_pct = st.number_input(
            "왕복 수수료/비용(%) (기본 0.2% 가정)",
            min_value=0.0, max_value=2.0,
            value=0.2, step=0.05,
        )

    cfg = get_mode_config(mode_name)

    prefix = (user_symbol or "").strip().upper().replace(" ", "")
    candidates = sorted(set(POPULAR_SYMBOLS + st.session_state["recent_symbols"]))
    suggestions = [s for s in candidates if s.startswith(prefix)] if prefix else []
    if suggestions:
        st.caption("자동완성 도움: " + ", ".join(suggestions[:6]))

    # 보유 정보
    col_mid1, col_mid2 = st.columns(2)
    avg_price = 0.0
    shares = 0
    if holding_type == "보유 중":
        with col_mid1:
            avg_price = st.number_input("내 평단가 (USD)", min_value=0.0, value=0.0, step=0.01)
        with col_mid2:
            shares = st.number_input("보유 수량 (주)", min_value=0, value=0, step=1)

    run_click = st.button("🚀 분석하기", key="run_analyze")

    run_from_side = st.session_state.get("run_from_side", False)
    run = run_click or run_from_side
    st.session_state["run_from_side"] = False

    if st.session_state.get("show_result") and st.session_state.get("analysis_params"):
        _p = st.session_state.get("analysis_params") or {}
        user_symbol = _p.get("user_symbol", user_symbol)
        holding_type = _p.get("holding_type", holding_type)
        mode_name = _p.get("mode_name", mode_name)
        commission_pct = _p.get("commission_pct", commission_pct)
        avg_price = float(_p.get("avg_price", avg_price or 0.0) or 0.0)
        shares = int(_p.get("shares", shares or 0) or 0)
        cfg = get_mode_config(mode_name)
        st.session_state["scroll_to_result"] = True
        st.session_state["show_result"] = True
        st.session_state["analysis_params"] = {
            "user_symbol": user_symbol,
            "holding_type": holding_type,
            "mode_name": mode_name,
            "commission_pct": commission_pct,
            "avg_price": avg_price,
            "shares": shares,
        }

    with st.expander("🛰 신규 진입 스캐너 (간단 버전)", expanded=False):
        col_s1, col_s2 = st.columns([1, 1])
        with col_s1:
            scan_click = st.button("📊 스캐너 실행", key="run_scan")
        with col_s2:
            close_scan = st.button("🧹 결과 닫기", key="close_scan")

        if close_scan:
            st.session_state["scan_results"] = None
            st.success("스캐너 결과를 닫았습니다.")
            st.rerun()

        if scan_click:
            with st.spinner("신규 진입 후보 종목 스캔 중..."):
                scan_mkt_score, scan_list = scan_new_entry_candidates(cfg)
            st.session_state["scan_results"] = {"market_score": scan_mkt_score, "items": scan_list}

        scan_data = st.session_state.get("scan_results")
        if scan_data:
            scan_mkt_score = scan_data["market_score"]
            scan_list = scan_data["items"]

            if scan_mkt_score <= -4:
                st.warning("시장 점수가 강한 Risk-off 구간입니다. 신규 진입은 특히 보수적으로.")

            if not scan_list:
                st.write("조건을 만족하는 신규 진입 후보 종목이 없습니다.")
            else:
                st.caption(f"총 **{len(scan_list)}개** 종목이 조건을 만족했습니다.")
                scan_clicked_symbol = None

                for item in scan_list:
                    sym = item["symbol"]
                    price = item["price"]
                    bias = item["bias"]
                    score_val = item["score"]
                    rr = item.get("rr")

                    rr_txt = f"{rr:.2f}:1" if rr is not None else "N/A"
                    st.markdown(
                        f"**{sym}** | 현재가 **{price:.2f}** | 단기흐름: {bias} | 스코어 **{score_val:.1f}** | 손익비 {rr_txt}"
                    )
                    go = st.button(f"🔍 {sym} 바로 분석", key=f"scan_go_{sym}")
                    if go:
                        scan_clicked_symbol = sym

                if scan_clicked_symbol is not None:
                    st.session_state["pending_symbol"] = scan_clicked_symbol
                    st.session_state["scroll_to_result"] = True
                    st.rerun()

    if not run:
        st.stop()

    symbol = normalize_symbol(user_symbol)
    display_name = user_symbol.strip() if user_symbol else ""

    if not symbol:
        st.error("❌ 종목 이름 또는 티커가 비어있습니다. 다시 입력해 주세요.")
        st.stop()

    with st.spinner("데이터 불러오는 중..."):
        ov = get_us_market_overview()
        fgi = ov.get("fgi")

        df = get_price_data(symbol, cfg["period"])
        if df.empty:
            st.error("❌ 이 종목은 선택한 기간 동안 데이터가 부족하거나, 티커가 잘못되었습니다.")
            st.stop()

        df = add_indicators(df)
        if df.empty:
            st.error("❌ 지표 계산에 필요한 데이터가 부족합니다.")
            st.stop()

        last = df.iloc[-1]
        df_5m = get_intraday_5m(symbol)

    if symbol not in st.session_state["recent_symbols"]:
        st.session_state["recent_symbols"].append(symbol)
        st.session_state["recent_symbols"] = st.session_state["recent_symbols"][-30:]

    price = float(last["Close"])
    profit_pct = (price - avg_price) / avg_price * 100 if avg_price > 0 else 0.0
    total_pnl = (price - avg_price) * shares if (shares > 0 and avg_price > 0) else 0.0

    buy_low, buy_high, tp0, tp1, tp2, sl0, sl1 = calc_levels(df, last, cfg)

    if holding_type == "신규 진입 검토" and buy_low is not None:
        sl0 = buy_low * 0.97
        sl1 = buy_low * 0.94

    rr = calc_rr_ratio(price, tp1, sl0)

    bias_comment = short_term_bias(last)
    gap_pct, gap_comment = calc_gap_info(df)
    atr14 = float(last["ATR14"]) if "ATR14" in last and not np.isnan(last["ATR14"]) else None
    price_move_abs = abs(float(last["Close"]) - float(last["Open"])) if atr14 is not None else None

    vp_levels = get_volume_profile(df)
    heavy_days = get_heavy_days(df)
    intraday_sc, intraday_comment = get_intraday_5m_score(df_5m)

    score_mkt, _, _ = compute_market_score(ov)
    alerts = build_risk_alerts(score_mkt, last, gap_pct, atr14, price_move_abs)

    ext_price = get_last_extended_price(symbol)

    is_fav = symbol in st.session_state["favorite_symbols"]
    fav_new = st.checkbox("⭐ 이 종목 즐겨찾기", value=is_fav)
    if fav_new and not is_fav:
        st.session_state["favorite_symbols"].append(symbol)
    elif (not fav_new) and is_fav:
        st.session_state["favorite_symbols"].remove(symbol)

    eff_avg_price = avg_price if holding_type == "보유 중" else 0.0
    signal = make_signal(last, eff_avg_price, cfg, fgi, main_tp=tp1, main_sl=sl0)

    st.markdown('<div id="analysis_result_anchor"></div>', unsafe_allow_html=True)
    if st.session_state.get("scroll_to_result", False):
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

    col_close1, col_close2 = st.columns([1, 6])
    with col_close1:
        if st.button("🧹 결과 닫기", key="close_result"):
            st.session_state["show_result"] = False
            st.session_state["analysis_params"] = None
            st.success("결과를 닫았습니다.")
            st.rerun()
    with col_close2:
        st.caption("※ 결과는 닫기 전까지 화면에 유지됩니다.")

    st.subheader("🧾 요약")
    st.write(f"- 입력 종목: **{display_name}** → 실제 티커: **{symbol}**")
    if fgi is not None:
        st.write(f"- 공포·탐욕지수(FGI, CNN): **{fgi:.1f}**")
    else:
        st.write("- 공포·탐욕지수(FGI): 조회 실패 → 시장심리는 제외하고 지표만 사용")

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
              <div class="small-muted">차트 기간: {cfg['period']} · 손절/익절: 추세·지지/저항 기반</div>
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
              <div class="small-muted">보유중이면 평단/수익률 계산, 신규진입이면 진입/손절 가정 표시</div>
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
        st.write(
            f"- 평가손익(수수료 {commission_pct:.2f}% 반영): "
            f"**{total_pnl_after_fee:,.2f} USD** (약 **{pnl_krw:,.0f} KRW**, 환율 {rate:,.2f}원 기준)"
        )

    st.subheader("🎯 매매 판단 (핵심)")
    col_sig1, col_sig2 = st.columns([2, 1])
    with col_sig1:
        st.write(f"**추천 액션:** ⭐ {signal} ⭐")
        st.write(f"**단기 방향성:** {bias_comment}")
    with col_sig2:
        if rr is not None:
            st.metric("손익비 (TP=1차 목표 / SL=0차 손절)", f"{rr:.2f} : 1")
            if rr >= 1.5:
                st.caption("👉 기술적 기준 손익비 양호")
            elif rr <= 1.0:
                st.caption("⚠ 손익비 불리 (손절폭이 상대적으로 큼)")
        else:
            st.caption("손익비 계산 불가 (TP/SL이 애매한 위치)")

    st.subheader("📌 가격 레벨 (진입/익절/손절 가이드)")

    if holding_type == "보유 중":
        if buy_low is not None and buy_high is not None:
            st.write(f"- 추가매수 관심 구간(추세 유지시): **{buy_low:.2f} ~ {buy_high:.2f} USD**")
        if tp0 is not None:
            st.write(f"- 0차 매도(부분 익절) 추천가: **{tp0:.2f} USD**")
        if tp1 is not None:
            st.write(f"- 1차 매도(주요 저항/목표): **{tp1:.2f} USD**")
        if tp2 is not None:
            st.write(f"- 2차 매도(확장 목표/과열 구간): **{tp2:.2f} USD**")
        if sl0 is not None:
            st.write(f"- 0차 손절가(추세 이탈 기준): **{sl0:.2f} USD**")
        if sl1 is not None:
            st.write(f"- 1차 손절가(최종 방어선): **{sl1:.2f} USD**")
    else:
        if buy_low is not None and buy_high is not None:
            entry1 = min(buy_high, buy_low * 1.03)
            entry2 = buy_low
            st.write(f"- 1차 진입(소량 매수) 추천가: **{entry1:.2f} USD** 근처")
            st.write(f"- 2차 분할매수(조정 시): **{entry2:.2f} USD** 이하 구간")
            st.caption("※ 신규 진입은 1·2차 분할 진입 기준입니다.")
        if sl0 is not None:
            st.write(f"- 기본 손절(매수 가설 실패): **{sl0:.2f} USD**")
        if sl1 is not None:
            st.write(f"- 최종 방어선: **{sl1:.2f} USD**")

    st.subheader("📊 갭 · 변동성 · 장중 흐름")
    col_gap, col_atr, col_intra = st.columns(3)
    with col_gap:
        if gap_pct is not None:
            st.metric("전일 대비 갭(시가 기준)", f"{gap_pct:.2f}%")
            st.caption(gap_comment)
        else:
            st.caption("갭 정보 계산 불가(데이터 부족)")

    with col_atr:
        if atr14 is not None:
            st.metric("ATR(14, 일봉)", f"{atr14:.2f}")
            if price_move_abs is not None and atr14 > 0:
                ratio = price_move_abs / atr14
                st.caption(f"오늘 캔들 몸통 크기: ATR의 {ratio:.2f}배")
        else:
            st.caption("ATR 계산 불가(데이터 부족)")

    with col_intra:
        if intraday_sc is not None:
            st.metric("장중 흐름 스코어 (0~4)", f"{intraday_sc}")
            st.caption(intraday_comment)
        else:
            st.caption(intraday_comment)

    st.subheader("🏗 매물대(최근 20일) & 큰손 추정 구간")
    col_vp1, col_vp2 = st.columns(2)
    with col_vp1:
        if vp_levels:
            st.markdown("**주요 매물대 (가격대별 거래량 상위)**")
            for lv in vp_levels:
                st.write(
                    f"- **{lv['low']:.2f} ~ {lv['high']:.2f} USD** (중심 {lv['mid']:.2f}) – 거래량 많은 구간"
                )
        else:
            st.caption("매물대 분석 데이터 부족")

    with col_vp2:
        if heavy_days:
            st.markdown("**큰손 추정 구간 (거래량 상위 일자)**")
            for h in heavy_days:
                st.write(f"- {h['date']} 종가 **{h['close']:.2f} USD** – 거래량 상위일")
        else:
            st.caption("거래량 상위 일자 추출 어려움")

    st.subheader("⚠ 리스크 경고 체크리스트")
    for a in alerts:
        st.write(a)

    # =====================================
    # 🤖 AI 해석 (요약 + 헷갈림 설명)  (기존 그대로)
    # =====================================
    st.subheader("🤖 AI 해석")
    st.caption("※ AI는 '확정 매수/매도 지시'가 아니라, 현재 신호가 왜 그렇게 보이는지(해석/설명)만 제공합니다.")

    try:
        cache_key = _ai_make_cache_key(symbol, holding_type, mode_name, avg_price, last, label_mkt)
    except Exception:
        cache_key = None

    cached = (cache_key is not None and cache_key in st.session_state.get("ai_cache", {}))
    btn_label = "🔁 AI 해석 다시 생성" if cached else "✨ AI 해석 보기"

    st.button(
        btn_label,
        key=f"ai_btn_{symbol}_{holding_type}_{mode_name}",
        on_click=request_ai_generation,
    )

    if st.session_state.get("ai_request", False):
        st.session_state["ai_request"] = False

        levels_dict = {
            "buy_low": buy_low, "buy_high": buy_high,
            "tp0": tp0, "tp1": tp1, "tp2": tp2,
            "sl0": sl0, "sl1": sl1,
        }

        extra_notes = [
            f"시장점수: {score_mkt} / label: {label_mkt}",
            f"신호: {signal}",
            f"단기흐름: {bias_comment}",
            f"갭: {gap_comment}",
        ]
        if rr is not None:
            extra_notes.append(f"손익비(RR): {rr:.2f}:1")
        if holding_type == "보유 중" and avg_price > 0:
            extra_notes.append(f"평단 대비: {(price/avg_price-1)*100:+.2f}%")
        if gap_pct is not None:
            extra_notes.append(f"갭%: {gap_pct:+.2f}%")
        if atr14 is not None:
            extra_notes.append(f"ATR14: {atr14:.2f}")

        with st.spinner("AI 해석 생성 중..."):
            ai_model_name = st.session_state.get("ai_model_name", "gpt-4o-mini")
            parsed, err = ai_summarize_and_explain(
                symbol=symbol,
                holding_type=holding_type,
                mode_name=mode_name,
                market_label=label_mkt,
                market_detail=detail_mkt,
                price=price,
                avg_price=avg_price,
                signal=signal,
                bias_comment=bias_comment,
                gap_comment=gap_comment,
                rr=rr,
                levels=levels_dict,
                last_row=last,
                extra_notes=extra_notes,
                model_name=ai_model_name,
            )
        if parsed:
            if cache_key:
                st.session_state["ai_cache"][cache_key] = parsed
            st.success("AI 해석 생성 완료!")
        else:
            st.error(err or "AI 생성 실패")

    ai_out = None
    if cache_key and cache_key in st.session_state.get("ai_cache", {}):
        ai_out = st.session_state["ai_cache"][cache_key]

    if ai_out is not None:
        one = str(ai_out.get("summary_one_line", "")).strip()
        blocks = ai_out.get("confusion_explain", [])

        if one:
            st.markdown(
                f"""
                <div class="card-soft">
                  <div class="layer-title-en">AI SUMMARY</div>
                  <div style="font-size:1.05rem;font-weight:700;line-height:1.35;">{one}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if isinstance(blocks, list) and blocks:
            blocks = blocks[:2]
            cols = st.columns(len(blocks))
            for i, b in enumerate(blocks):
                title = str(b.get("title", "")).strip()
                desc = str(b.get("desc", "")).strip()
                with cols[i]:
                    st.markdown(
                        f"""
                        <div class="card-soft-sm">
                          <div style="font-weight:700;margin-bottom:6px;">{title}</div>
                          <div class="small-muted" style="line-height:1.45;">{desc}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
    else:
        st.info("AI 해석은 버튼을 누를 때만 생성됩니다. (Streamlit Secrets에 OPENAI_API_KEY가 있어야 합니다.)")

    st.subheader("📈 가격/볼린저밴드 차트 (단순 표시)")
    chart_df = df[["Close", "MA20", "BBL", "BBU"]].tail(120)
    st.line_chart(chart_df)
