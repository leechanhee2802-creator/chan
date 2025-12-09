import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests

# =====================================
# 페이지 설정 + 전체 테마
# =====================================
st.set_page_config(
    page_title="내 주식 자동판독기 (시장 개요 + 실전 보조지표)",
    page_icon="📈",
    layout="wide",
)

# 대시보드 스타일 CSS (폰트/폰트크기는 유지, 배경은 라이트톤으로 변경)
st.markdown(
    """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

/* 전체 폰트 */
* {
    font-family: "Pretendard", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
}

/* 앱 배경을 밝게 */
[data-testid="stAppViewContainer"] {
    background: #f3f4f6;
}

/* 메인 컨테이너 */
main.block-container {
    padding-top: 1.3rem;
    padding-bottom: 2rem;
    max-width: 1350px;
    background-color: transparent;
}

/* 헤더/사이드바도 라이트톤 */
header, [data-testid="stHeader"] {
    background-color: #ffffff !important;
}
[data-testid="stSidebar"] {
    background-color: #f9fafb !important;
}

/* 카드/탭 패널 */
[data-baseweb="tab-panel"], section, article {
    background-color: transparent !important;
}

/* 헤더 사이즈/색 (이전 버전 유지) */
h1 {
    color: #111827 !important;
    font-size: 1.6rem !important;
    font-weight: 600 !important;
}
h2 {
    color: #111827 !important;
    font-size: 1.25rem !important;
    font-weight: 600 !important;
}
h3 {
    color: #111827 !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
}
h4 {
    color: #111827 !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
}

/* 구분선 */
hr {
    margin-top: 1rem;
    margin-bottom: 1rem;
    border: 0;
    border-top: 1px solid #e5e7eb;
}

/* 카드 박스 – 라이트 테마 */
.card {
    background: #ffffff;
    border-radius: 16px;
    padding: 14px 18px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 4px 10px rgba(15, 23, 42, 0.08);
}
.card-title {
    font-size: 0.78rem;
    color: #6b7280 !important;
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.card-value {
    font-size: 1.4rem;
    font-weight: 600;
    color: #111827 !important;
    margin-bottom: 4px;
}
.card-sub {
    font-size: 0.86rem;
    color: #4b5563 !important;
}

/* 작은 카드 */
.card-small {
    background: #ffffff;
    border-radius: 14px;
    padding: 10px 12px;
    border: 1px solid #e5e7eb;
}

/* expander */
details {
    border-radius: 16px !important;
    border: 1px solid #e5e7eb !important;
    background-color: #ffffff !important;
    box-shadow: 0 4px 10px rgba(15, 23, 42, 0.08);
}

/* metric 카드 – 라이트톤 */
[data-testid="metric-container"] {
    background-color: #ffffff;
    border-radius: 14px;
    padding: 10px 14px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 4px 10px rgba(15, 23, 42, 0.08);
}
[data-testid="stMetricLabel"] {
    color: #6b7280 !important;
}
[data-testid="stMetricValue"] {
    color: #111827 !important;
}

/* 버튼 (즐겨찾기/최근 포함) */
.stButton>button {
    border-radius: 999px;
    padding: 6px 18px;
    font-size: 0.9rem;
    border: 1px solid #d1d5db;
    background: #ffffff;
    color: #111827 !important;
}
.stButton>button:hover {
    border-color: #38bdf8;
    background: #eff6ff;
}

/* 입력 박스 */
[data-baseweb="input"] > div {
    background-color: #ffffff !important;
    border-radius: 999px !important;
}
[data-baseweb="input"] input {
    background-color: transparent !important;
    color: #111827 !important;
}
textarea {
    background-color: #ffffff !important;
    color: #111827 !important;
}
input::placeholder, textarea::placeholder {
    color: #9ca3af !important;
}

/* selectbox / radio */
[data-baseweb="select"] > div {
    background-color: #ffffff !important;
}
[data-baseweb="radio"] > label {
    background-color: transparent !important;
}

/* 탭 헤더 */
[data-baseweb="tab-list"] {
    background-color: #e5e7eb;
    border-radius: 999px;
    padding: 4px;
}
[data-baseweb="tab"] {
    border-radius: 999px !important;
}

/* 표/데이터프레임 */
[data-testid="stDataFrame"], [data-testid="stTable"] {
    background-color: #ffffff;
}

/* 캡션/작은 글씨 */
.small-muted {
    font-size: 0.8rem;
    color: #6b7280 !important;
}

/* 오른쪽 즐겨찾기/최근 버튼 */
.sidebar-button {
    width: 100%;
    text-align: left;
}
</style>
    """,
    unsafe_allow_html=True,
)

# =====================================
# 한글 이름 → 티커 매핑
# =====================================
KOREAN_TICKER_MAP = {
    # 빅테크 / AI (미국)
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

    # 소비 / 리테일
    "코카콜라": "KO", "펩시": "PEP",
    "맥도날드": "MCD", "스타벅스": "SBUX",
    "나이키": "NKE", "월마트": "WMT", "코스트코": "COST",

    # 헬스케어
    "존슨앤존슨": "JNJ", "존슨앤드존슨": "JNJ",
    "화이자": "PFE", "모더나": "MRNA",
    "유나이티드헬스": "UNH", "메르크": "MRK", "애브비": "ABBV",

    # 금융
    "JP모건": "JPM", "제이피모건": "JPM",
    "골드만삭스": "GS", "모건스탠리": "MS",
    "뱅크오브아메리카": "BAC",
    "씨티": "C", "씨티그룹": "C",
    "페이팔": "PYPL",

    # 에너지 / 산업 / 통신
    "엑슨모빌": "XOM", "셰브론": "CVX",
    "캐터필러": "CAT", "3M": "MMM",
    "허니웰": "HON", "디즈니": "DIS",
    "버라이즌": "VZ", "AT&T": "T",

    # 데이터베이스 / 소프트웨어
    "오라클": "ORCL",

    # 코인 / 채굴주
    "코인베이스": "COIN", "코인베이스글로벌": "COIN",
    "마이크로스트래티지": "MSTR",
    "리오트": "RIOT", "라이엇": "RIOT",
    "마라톤디지털": "MARA", "마라톤": "MARA",
    "클린스파크": "CLSK",
    "비트팜": "BITF",
    "갤럭시디지털": "BRPHF",

    # 대표 ETF
    "QQQ": "QQQ", "나스닥ETF": "QQQ", "나스닥100": "QQQ",
    "SPY": "SPY", "S&P500": "SPY", "SP500": "SPY",
    "VOO": "VOO", "S&P인덱스": "VOO",

    # 레버리지 / 인버스
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

    # 비트코인 ETF
    "비트코인ETF": "IBIT",
    "아이쉐어즈비트코인": "IBIT",
}

POPULAR_SYMBOLS = [
    "NVDA", "META", "TSLA", "AAPL", "MSFT", "AMZN",
    "QQQ", "TQQQ", "SOXL", "SPY", "VOO",
    "COIN", "MSTR", "RIOT", "MARA",
    "ORCL", "PYPL", "NFLX", "PLTR", "AVGO",
]

BIG_TECH = ["NVDA", "AAPL", "MSFT", "AMZN", "META", "GOOGL", "TSLA"]
SECTOR_ETFS = {
    "기술주 (XLK)": "XLK",
    "반도체 (SOXX)": "SOXX",
    "금융 (XLF)": "XLF",
    "헬스케어 (XLV)": "XLV",
    "에너지 (XLE)": "XLE",
    "커뮤니케이션 (XLC)": "XLC",
}

def normalize_symbol(user_input: str) -> str:
    name = user_input.strip()
    if name in KOREAN_TICKER_MAP:
        return KOREAN_TICKER_MAP[name]
    return name.replace(" ", "").upper()

# =====================================
# 색상 강화용: 상승/하락 퍼센트 HTML 포맷
# =====================================
def format_change_html(chg: float | None) -> str:
    if chg is None:
        return '<span>-</span>'
    if chg > 0:
        return f'<span style="color:#b91c1c;">+{chg:.2f}%</span>'   # 빨강(상승)
    elif chg < 0:
        return f'<span style="color:#1d4ed8;">{chg:.2f}%</span>'   # 파랑(하락)
    else:
        return f'<span>{chg:.2f}%</span>'

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

# =====================================
# 미국 시장 개요
# =====================================
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

@st.cache_data(ttl=60)
def get_us_market_overview():
    overview = {}

    # 선물
    nq_last, nq_chg, nq_state = safe_last_change_info("NQ=F")
    es_last, es_chg, es_state = safe_last_change_info("ES=F")
    overview["futures"] = {
        "nasdaq": {"last": nq_last, "chg_pct": nq_chg, "state": nq_state},
        "sp500": {"last": es_last, "chg_pct": es_chg, "state": es_state},
    }

    # 금리 / 달러
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

    # ETF 3종
    etfs = [
        get_etf_price_with_prepost("QQQ", "QQQ (나스닥100 ETF)"),
        get_etf_price_with_prepost("VOO", "VOO (S&P500 ETF)"),
        get_etf_price_with_prepost("SOXX", "SOXX (반도체 ETF)"),
    ]
    overview["etfs"] = etfs

    overview["fgi"] = fetch_fgi()

    return overview

@st.cache_data(ttl=60)
def get_bigtech_overview():
    data = []
    score = 0
    for s in BIG_TECH:
        last, chg, _ = safe_last_change_info(s)
        if last is None or chg is None:
            continue
        data.append({"symbol": s, "chg": chg})
        if chg >= 2:
            score += 2
        elif chg >= 0.5:
            score += 1
        elif chg <= -2:
            score -= 2
        elif chg <= -0.5:
            score -= 1
    if not data:
        return None, []
    return score, data

@st.cache_data(ttl=60)
def get_sector_overview():
    rows = []
    score = 0
    for name, sym in SECTOR_ETFS.items():
        last, chg, _ = safe_last_change_info(sym)
        if last is None or chg is None:
            continue
        rows.append({"name": name, "symbol": sym, "chg": chg})
        if chg >= 1:
            score += 1
        elif chg <= -1:
            score -= 1
    if not rows:
        return None, []
    return score, rows

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
            score += 2
            details.append(f"나스닥 선물 +{nas_chg:.2f}% (강한 상승)")
        elif nas_chg >= 0.3:
            score += 1
            details.append(f"나스닥 선물 +{nas_chg:.2f}% (완만한 상승)")
        elif nas_chg <= -1.0:
            score -= 2
            details.append(f"나스닥 선물 {nas_chg:.2f}% (강한 하락)")
        elif nas_chg <= -0.3:
            score -= 1
            details.append(f"나스닥 선물 {nas_chg:.2f}% (완만한 하락)")

    us10y = rf.get("us10y")
    if us10y is not None:
        if us10y < 4.0:
            score += 2
            details.append(f"미 10년물 {us10y:.2f}% (금리 우호)")
        elif us10y < 4.2:
            score += 1
            details.append(f"미 10년물 {us10y:.2f}% (무난)")
        elif us10y > 4.4:
            score -= 2
            details.append(f"미 10년물 {us10y:.2f}% (금리 부담)")
        else:
            score -= 1
            details.append(f"미 10년물 {us10y:.2f}% (다소 부담)")

    dxy = rf.get("dxy")
    if dxy is not None:
        if dxy < 104:
            score += 1
            details.append(f"DXY {dxy:.2f} (달러 약세 → Risk-on 우호)")
        elif dxy > 106:
            score -= 1
            details.append(f"DXY {dxy:.2f} (달러 강세 → Risk-off 경계)")

    for e in etfs:
        sym = e.get("symbol")
        chg = e.get("chg_pct")
        if chg is None:
            continue
        if chg >= 0.5:
            score += 1
            details.append(f"{sym} +{chg:.2f}% (ETF 강세)")
        elif chg <= -0.5:
            score -= 1
            details.append(f"{sym} {chg:.2f}% (ETF 약세)")

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

    detail_text = " · ".join(details)
    return score, label, detail_text

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
    rsi = 100 - (100 / (1 + rs))
    df["RSI14"] = rsi

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
# 코멘트 함수들
# =====================================
def comment_rsi(rsi):
    if rsi < 30:
        return "강한 과매도"
    elif rsi < 40:
        return "약한 과매도"
    elif rsi < 60:
        return "중립"
    elif rsi < 70:
        return "약한 과열"
    else:
        return "강한 과열"

def comment_stoch(k, d):
    if k > 80 and d > 80:
        return "과열권"
    elif k < 20 and d < 20:
        return "침체/과매도권"
    elif k > d and k > 50:
        return "상승 모멘텀"
    elif k < d and k < 50:
        return "하락 모멘텀"
    else:
        return "중립"

def comment_macd(macd, signal):
    if macd > 0 and macd > signal:
        return "상승 모멘텀 우위"
    elif macd < 0 and macd < signal:
        return "하락 모멘텀 우위"
    elif macd > signal:
        return "골든크로스(상방 전환 시도)"
    elif macd < signal:
        return "데드크로스(하방 전환 시도)"
    else:
        return "중립"

def comment_bb(price, bbl, bbu, ma20):
    if price > bbu:
        return "밴드 상단 돌파(과열/급등 구간)"
    elif price > ma20:
        return "상단 영역(강세 추세)"
    elif price < bbl:
        return "밴드 하단 이탈(과매도/급락 구간)"
    else:
        return "중단~하단 영역(조정/중립)"

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

    if price > ma20:
        score += 1
    else:
        score -= 1

    if price > ma5:
        score += 1
    else:
        score -= 1

    if macd > macds:
        score += 1
    else:
        score -= 1

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

# =====================================
# 매매 신호 / 레벨 등
# =====================================
def get_mode_config(mode_name: str):
    if mode_name == "단타":
        return {"name": "단타", "period": "3mo", "take_profit_pct": 7, "stop_loss_pct": 10}
    elif mode_name == "장기":
        return {"name": "장기", "period": "1y", "take_profit_pct": 25, "stop_loss_pct": 30}
    else:
        return {"name": "스윙", "period": "6mo", "take_profit_pct": 12, "stop_loss_pct": 20}

def make_signal(row, avg_price, cfg, fgi=None):
    price = float(row["Close"])
    bbl = float(row["BBL"])
    bbu = float(row["BBU"])
    ma20 = float(row["MA20"])
    k = float(row["STOCH_K"])
    d = float(row["STOCH_D"])
    macd = float(row["MACD"])
    macds = float(row["MACD_SIGNAL"])
    rsi = float(row["RSI14"])

    take_profit_pct = cfg["take_profit_pct"]
    stop_loss_pct = cfg["stop_loss_pct"]

    if avg_price > 0:
        profit_pct = (price - avg_price) / avg_price * 100
    else:
        profit_pct = 0.0

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

    base_buy_cond = (strong_oversold and profit_pct > -stop_loss_pct)
    if fear and price < bbl * 1.02 and k < 30 and rsi < 45 and profit_pct > -stop_loss_pct * 1.2:
        return "분할매수 (공포 국면)"
    elif greed and price < bbl * 0.98 and k < 15 and rsi < 30 and profit_pct > -stop_loss_pct:
        return "분할매수"
    elif base_buy_cond:
        return "분할매수"

    loss_pct = -profit_pct if avg_price > 0 else 0.0
    lower_bound = stop_loss_pct
    upper_bound = stop_loss_pct + 10

    oversold_signals = 0
    if rsi < 30:
        oversold_signals += 1
    if k < 20 and d < 20:
        oversold_signals += 1
    if price < bbl * 1.02:
        oversold_signals += 1
    if macd > macds:
        oversold_signals += 1

    rational_loss = (loss_pct >= lower_bound and loss_pct <= upper_bound)
    rational_oversold = (oversold_signals >= 2)

    if rational_loss and rational_oversold:
        return "합리적 물타기 분할매수"

    hit_target = (profit_pct >= take_profit_pct)
    if hit_target and (strong_overbought or (greed and mild_overbought)):
        return "강한 부분매도 (수익+과열)"
    if hit_target:
        return "부분매도 (수익 목표 도달)"
    if strong_overbought or (greed and mild_overbought):
        return "위험주의 (지표 과열 대비 수익 낮음)"

    if profit_pct <= -stop_loss_pct:
        return "손절 or 비중축소 고려"

    return "관망"

def calc_levels(df, last, avg_price, cfg):
    recent = df.tail(20)
    recent_high = float(recent["Close"].max())
    recent_low = float(recent["Close"].min())

    price = float(last["Close"])
    ma20 = float(last["MA20"])
    bbl = float(last["BBL"])
    bbu = float(last["BBU"])

    take_profit_pct = cfg["take_profit_pct"]
    stop_loss_pct = cfg["stop_loss_pct"]

    if price > ma20:
        buy_low = ma20 * 0.98
        buy_high = ma20 * 1.01
    else:
        buy_low = bbl * 0.98
        buy_high = bbl * 1.02

    tp0_pct = take_profit_pct * 0.6
    tp1_pct = take_profit_pct
    tp2_pct = take_profit_pct * 1.8

    if avg_price > 0:
        base0 = avg_price * (1 + tp0_pct / 100)
        base1 = avg_price * (1 + tp1_pct / 100)
        base2 = avg_price * (1 + tp2_pct / 100)
    else:
        base0 = price * (1 + tp0_pct / 100)
        base1 = price * (1 + tp1_pct / 100)
        base2 = price * (1 + tp2_pct / 100)

    tp0 = max(base0, recent_high * 0.97, ma20 * 1.02)
    tp1 = max(base1, recent_high * 0.99, bbu * 0.98, tp0 * 1.02)
    tp2 = max(base2, recent_high * 1.01, bbu * 1.01, tp1 * 1.03)

    if avg_price > 0:
        mode_stop = avg_price * (1 - stop_loss_pct / 100)
    else:
        mode_stop = price * (1 - stop_loss_pct / 100)

    sl0 = mode_stop
    deep_candidate = min(recent_low * 0.99, bbl * 0.97)
    sl1 = min(sl0 * 0.97, deep_candidate)

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

def calc_technical_tp_sl(df: pd.DataFrame):
    recent = df.tail(20)
    if len(recent) < 5:
        return None, None

    last = recent.iloc[-1]
    price = float(last["Close"])
    recent_high = float(recent["Close"].max())
    recent_low = float(recent["Close"].min())
    ma20 = float(last["MA20"])
    bbl = float(last["BBL"])
    bbu = float(last["BBU"])

    tp_candidates = [
        recent_high * 0.99,
        bbu * 0.98,
        ma20 * 1.03,
    ]
    tech_tp = max(tp_candidates)

    sl_candidates = [
        recent_low * 1.01,
        bbl * 1.01,
    ]
    tech_sl = min(sl_candidates)

    if tech_tp <= price or tech_sl >= price:
        return None, None

    return tech_tp, tech_sl

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

    levels_sorted = sorted(levels, key=lambda x: x["volume"], reverse=True)
    return levels_sorted[:3]

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
                label = sym
                if sym in KOREAN_TICKER_MAP.values():
                    ko_names = [k for k, v in KOREAN_TICKER_MAP.items() if v == sym]
                    if ko_names:
                        label = f"{sym} ({ko_names[0]})"
                if st.button(label, key=f"fav_{sym}"):
                    clicked_symbol = sym

    with tab_recent:
        recents = list(reversed(st.session_state["recent_symbols"]))
        if not recents:
            st.caption("최근 조회 종목이 없습니다.")
        else:
            for sym in recents:
                label = sym
                if sym in KOREAN_TICKER_MAP.values():
                    ko_names = [k for k, v in KOREAN_TICKER_MAP.items() if v == sym]
                    if ko_names:
                        label = f"{sym} ({ko_names[0]})"
                if st.button(label, key=f"recent_{sym}"):
                    clicked_symbol = sym

    if clicked_symbol:
        st.session_state["selected_symbol"] = clicked_symbol
        st.session_state["symbol_input"] = clicked_symbol
        st.session_state["run_from_side"] = True

# ---- 왼쪽: 메인 ----
with col_main:
    st.title("📈 내 주식 자동판독기")
    st.caption("시장 개요 + 개별 종목 판독 + 손익비/갭/ATR/장중 흐름까지 한 화면에서 확인")

    # 1) 미국 시장 개요
    with st.expander("🌍 미국 시장 실시간 흐름 (보조지표)", expanded=True):
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            refresh = st.button("🔄 새로고침", key="refresh_overview")
        if refresh:
            get_us_market_overview.clear()
            get_bigtech_overview.clear()
            get_sector_overview.clear()

        with st.spinner("미국 선물 · 금리 · 달러 · ETF · 빅테크 · 섹터 상황 불러오는 중..."):
            ov = get_us_market_overview()
            bt_score, bt_data = get_bigtech_overview()
            sec_score, sec_data = get_sector_overview()

        score_mkt, label_mkt, detail_mkt = compute_market_score(ov)

        fut = ov.get("futures", {})
        rf = ov.get("rates_fx", {})
        etfs = ov.get("etfs", [])

        nas = fut.get("nasdaq", {})
        es = fut.get("sp500", {})

        col1, col2, col3 = st.columns(3)
        with col1:
            last = nas.get("last")
            chg = nas.get("chg_pct")
            if last is not None and chg is not None:
                st.metric("나스닥 선물", f"{last:.1f}", f"{chg:.2f}%")
            else:
                st.metric("나스닥 선물", "N/A", "-")
        with col2:
            last = es.get("last")
            chg = es.get("chg_pct")
            if last is not None and chg is not None:
                st.metric("S&P500 선물", f"{last:.1f}", f"{chg:.2f}%")
            else:
                st.metric("S&P500 선물", "N/A", "-")
        with col3:
            st.metric("시장 점수", f"{score_mkt} / 8", label_mkt)
            st.caption(
                '<span class="small-muted">(범위: -8 ~ 8 | 선물·금리·달러·ETF 기준 종합)</span>',
                unsafe_allow_html=True,
            )

        if detail_mkt:
            st.caption("· " + detail_mkt)

        st.markdown("<hr>", unsafe_allow_html=True)

        col4, col5, col6 = st.columns(3)
        with col4:
            us10y = rf.get("us10y")
            us10y_chg = rf.get("us10y_chg")
            if us10y is not None:
                delta = f"{us10y_chg:.3f}p" if us10y_chg is not None else ""
                st.metric("미 10년물", f"{us10y:.2f}%", delta)
            else:
                st.metric("미 10년물", "N/A", "")
        with col5:
            dxy = rf.get("dxy")
            dxy_chg = rf.get("dxy_chg")
            if dxy is not None and dxy_chg is not None:
                st.metric("달러 인덱스 (DXY)", f"{dxy:.2f}", f"{dxy_chg:.2f}%")
            else:
                st.metric("달러 인덱스 (DXY)", "N/A", "-")
        with col6:
            st.write("")
            st.caption(
                '<span class="small-muted">※ 수치는 약간의 지연이 있을 수 있습니다.</span>',
                unsafe_allow_html=True,
            )

        st.markdown("<hr>", unsafe_allow_html=True)

        # ETF
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

                    value_str = f"{current:.2f}" if current is not None else "N/A"
                    delta = f"{chg:.2f}%" if chg is not None else "-"

                    st.metric(sym, value_str, delta)
                    extra = basis
                    if state:
                        extra += f" · 상태: {state}"
                    st.caption(extra)
            st.caption(
                '<span class="small-muted">※ %는 전일 종가 대비 기준입니다.</span>',
                unsafe_allow_html=True,
            )
        else:
            st.write("ETF 데이터를 불러오지 못했습니다.")

        st.markdown("<hr>", unsafe_allow_html=True)

        # 💡 빅테크 레이어
        st.markdown("**💡 빅테크 레이어 (NVDA/AAPL/MSFT/AMZN/META/GOOGL/TSLA)**")
        if bt_data:
            bt_col1, bt_col2 = st.columns([1, 2])
            with bt_col1:
                st.metric("빅테크 강도 점수", f"{bt_score}", "상승+ / 하락-")
            with bt_col2:
                parts = []
                for d in bt_data:
                    parts.append(
                        f"{d['symbol']}: {format_change_html(d['chg'])}"
                    )
                st.markdown(" · ".join(parts), unsafe_allow_html=True)
        else:
            st.caption("빅테크 데이터를 불러오지 못했습니다.")

        st.markdown("<hr>", unsafe_allow_html=True)

        # 🏗 섹터 로테이션 레이어
        st.markdown("**🏗 섹터 로테이션 레이어 (대표 섹터 ETF)**")
        if sec_data:
            sec_col1, sec_col2 = st.columns([1, 2])
            with sec_col1:
                st.metric("섹터 점수", f"{sec_score}", "성장+ / 방어-")
            with sec_col2:
                parts = []
                for row in sec_data:
                    parts.append(
                        f"{row['name']}: {format_change_html(row['chg'])}"
                    )
                st.markdown(" · ".join(parts), unsafe_allow_html=True)
            st.caption(
                '<span class="small-muted">※ 섹터별 강도 흐름을 통해 성장/방어/에너지 쏠림을 한 눈에 체크.</span>',
                unsafe_allow_html=True,
            )
        else:
            st.caption("섹터 ETF 데이터를 불러오지 못했습니다.")

    st.markdown("<hr>", unsafe_allow_html=True)

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
            min_value=0.0,
            max_value=2.0,
            value=0.2,
            step=0.05,
        )

    prefix = user_symbol.strip().upper().replace(" ", "")
    candidates = sorted(set(POPULAR_SYMBOLS + st.session_state["recent_symbols"]))
    suggestions = []
    if prefix:
        suggestions = [s for s in candidates if s.startswith(prefix)]
    if suggestions:
        st.caption("자동완성 도움: " + ", ".join(suggestions[:6]))

    col_mid1, col_mid2 = st.columns(2)
    avg_price = 0.0
    shares = 0
    if holding_type == "보유 중":
        with col_mid1:
            avg_price = st.number_input("내 평단가 (USD)", min_value=0.0, value=0.0, step=0.01)
        with col_mid2:
            shares = st.number_input("보유 수량 (주)", min_value=0, value=0, step=1)

    run_click = st.button("🚀 분석하기", key="run_analyze")
    run = run_click or st.session_state.get("run_from_side", False)
    st.session_state["run_from_side"] = False

    if not run:
        st.stop()

    symbol = normalize_symbol(user_symbol)
    display_name = user_symbol
    st.session_state["selected_symbol"] = user_symbol

    if not symbol:
        st.error("❌ 종목 이름 또는 티커가 비어있습니다. 다시 입력해 주세요.")
        st.stop()

    cfg = get_mode_config(mode_name)

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

    eff_avg_price = avg_price if holding_type == "보유 중" else 0.0
    signal = make_signal(last, eff_avg_price, cfg, fgi)
    buy_low, buy_high, tp0, tp1, tp2, sl0, sl1 = calc_levels(df, last, eff_avg_price, cfg)
    bias_comment = short_term_bias(last)

    gap_pct, gap_comment = calc_gap_info(df)
    atr14 = float(last["ATR14"]) if "ATR14" in last and not np.isnan(last["ATR14"]) else None
    if atr14 is not None:
        price_move_abs = abs(float(last["Close"]) - float(last["Open"]))
    else:
        price_move_abs = None

    tech_tp, tech_sl = calc_technical_tp_sl(df)

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

    # ==========================
    # UI 출력
    # ==========================
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
            st.caption(
                f"시외/프리·애프터 포함 최근가: {ext_price:.2f} ({sign}{diff_pct:.2f}%)"
            )
    with col_b:
        st.markdown(
            f"""
<div class="card">
  <div class="card-title">MODE</div>
  <div class="card-value">{cfg['name']} 모드</div>
  <div class="card-sub">차트 기간: {cfg['period']} · 손절: -{cfg['stop_loss_pct']}% · 익절: +{cfg['take_profit_pct']}%</div>
</div>
""",
            unsafe_allow_html=True,
        )
    with col_c:
        st.markdown(
            f"""
<div class="card">
  <div class="card-title">POSITION</div>
  <div class="card-sub">보유 상태: <b>{holding_type}</b></div>
  <div class="card-sub">평단/수익률은 보유중일 때만 계산됩니다.</div>
</div>
""",
            unsafe_allow_html=True,
        )

    if holding_type == "보유 중" and avg_price > 0:
        color_html = format_change_html(profit_pct)
        st.markdown(f"- 평단가: **{avg_price:.2f} USD**", unsafe_allow_html=True)
        st.markdown(f"- 수익률: {color_html}", unsafe_allow_html=True)
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
        # 신규 진입 모드일 때: 리스크/리워드 요약 (손익비 숫자 대신 위/아래 %만)
        if holding_type == "신규 진입 검토" and tech_tp is not None and tech_sl is not None:
            up_pct = (tech_tp - price) / price * 100
            down_pct = (price - tech_sl) / price * 100
            up_html = format_change_html(up_pct)
            down_html = format_change_html(-down_pct)  # 하락은 음수로
            st.markdown("**신규 진입 관점 리스크·리워드**", unsafe_allow_html=True)
            st.markdown(f"- 위쪽 잠재 수익 여지: {up_html}", unsafe_allow_html=True)
            st.markdown(f"- 아래쪽 기술적 손실 여지: {down_html}", unsafe_allow_html=True)
            st.caption("※ 순수 기술적 TP/SL 기준으로 산출된 대략적인 위/아래 폭입니다.")

    st.subheader("📌 가격 레벨 (진입/익절/손절 가이드)")

    # 🎯 전략 기반 레벨 (내 모드 기준)
    st.markdown("**🎯 전략 기반 레벨 (내 단타/스윙/장기 설정 기준)**")
    if holding_type == "보유 중":
        st.write(f"- 매수/추가매수 구간: **{buy_low:.2f} ~ {buy_high:.2f} USD**")
        st.write(f"- 0차 매도 추천가: **{tp0:.2f} USD**")
        st.write(f"- 1차 매도 추천가: **{tp1:.2f} USD**")
        st.write(f"- 2차 매도 추천가: **{tp2:.2f} USD**")
        st.write(f"- 0차 손절가: **{sl0:.2f} USD**")
        st.write(f"- 1차 손절가(최종 방어선): **{sl1:.2f} USD**")
    else:
        entry1 = min(buy_high, buy_low * 1.03)
        entry2 = buy_low
        st.write(f"- 1차 진입(소량 매수) 추천가: **{entry1:.2f} USD** 근처")
        st.write(f"- 2차 분할매수(조정 시): **{entry2:.2f} USD** 이하 구간")
        st.caption("※ 신규 진입은 1·2차로 나누어 분할 매수하는 기준입니다.")

    # 🧪 기술적 TP/SL
    st.markdown("**🧪 기술적 TP/SL (순수 차트 기준)**")
    if tech_tp is not None and tech_sl is not None:
        up_pct = (tech_tp - price) / price * 100
        down_pct = (price - tech_sl) / price * 100
        up_html = format_change_html(up_pct)
        down_html = format_change_html(-down_pct)
        st.write(f"- 기술적 TP(목표가격) 대략: **{tech_tp:.2f} USD** ({up_html})", unsafe_allow_html=True)
        st.write(f"- 기술적 SL(손절라인) 대략: **{tech_sl:.2f} USD** ({down_html})", unsafe_allow_html=True)
        st.caption("※ 최근 고저/볼린저밴드/평균선 기준으로 자동 산출된 순수 차트 레벨입니다.")
    else:
        st.caption("기술적 TP/SL을 계산하기에 데이터가 부족하거나, 현재 위치가 애매합니다.")

    st.subheader("📊 갭 · 변동성 · 장중 흐름")
    col_gap, col_atr, col_intra = st.columns(3)
    with col_gap:
        if gap_pct is not None:
            st.metric("전일 대비 갭(시가 기준)", f"{gap_pct:.2f}%")
            st.caption(gap_comment)
        else:
            st.caption("갭 정보를 계산하기에 데이터가 부족합니다.")

    with col_atr:
        if atr14 is not None:
            st.metric("ATR(14, 일봉)", f"{atr14:.2f}")
            if price_move_abs is not None and atr14 > 0:
                ratio = price_move_abs / atr14
                st.caption(f"오늘 캔들 몸통 크기: ATR의 {ratio:.2f}배")
        else:
            st.caption("ATR 계산 불가 (데이터 부족)")

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
                    f"- **{lv['low']:.2f} ~ {lv['high']:.2f} USD** (중심 {lv['mid']:.2f}) – "
                    f"최근 20일 중 거래량 많았던 구간"
                )
        else:
            st.caption("매물대 분석을 하기에는 데이터가 부족합니다.")
    with col_vp2:
        if heavy_days:
            st.markdown("**큰손 추정 구간 (거래량 상위 일자)**")
            for h in heavy_days:
                st.write(
                    f"- {h['date']} 종가 **{h['close']:.2f} USD** – 거래량 상위일(대량 수급 가능성)"
                )
        else:
            st.caption("거래량 상위 일자를 찾기 어렵습니다.")

    st.subheader("⚠ 리스크 경고 체크리스트")
    for a in alerts:
        st.write(a)

    st.subheader("📈 가격 / 볼린저밴드 차트 (최근 약 6개월)")
    chart_df = df[["Close", "MA20", "BBL", "BBU"]].tail(120)
    st.line_chart(chart_df)

if __name__ == "__main__":
    pass
