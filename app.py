import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import numpy as np
import time
from yfinance.exceptions import YFRateLimitError

# -------------------------------
# 한글 이름 → 티커 매핑 (미국 위주)
# -------------------------------
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

    # 코인 관련 / 채굴주 / 비트코인 노출주
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

    # 레버리지 / 인버스 ETF
    "SOXL": "SOXL", "반도체3배": "SOXL",
    "SOXS": "SOXS", "반도체인버스3배": "SOXS",
    "TQQQ": "TQQQ", "나스닥3배": "TQQQ",
    "SQQQ": "SQQQ", "나스닥인버스3배": "SQQQ",
    "TECL": "TECL", "기술주3배": "TECL",
    "SPXL": "SPXL", "S&P3배": "SPXL",
    "SPXS": "SPXS", "S&P인버스3배": "SPXS",
    "LABU": "LABU", "바이오3배": "LABU",
    "LABD": "LABD", "바이오인버스3배": "LABD",
    "ARKK": "ARKK", "아크": "ARKK", "아크K": "ARKK",

    # 비트코인 ETF (미국)
    "비트코인ETF": "IBIT",
    "아이쉐어즈비트코인": "IBIT",
}

# 인기 종목 (자동완성 힌트용)
POPULAR_SYMBOLS = [
    "NVDA", "META", "TSLA", "AAPL", "MSFT", "AMZN",
    "QQQ", "TQQQ", "SOXL", "SPY", "VOO",
    "COIN", "MSTR", "RIOT", "MARA",
    "ORCL", "PYPL", "NFLX", "PLTR", "AVGO",
]

# 스캐너 유니버스 (AI/데이터센터/클라우드/러셀2000까지 확장)
SCAN_UNIVERSE = {
    # 메가테크 / 반도체 / AI 인프라
    "NVDA": "엔비디아",
    "AMD": "AMD",
    "AVGO": "브로드컴",
    "TSM": "TSMC",
    "INTC": "인텔",
    "QCOM": "퀄컴",
    "MU": "마이크론",
    "SMCI": "슈퍼마이크로",
    "ASML": "ASML",
    "ADBE": "어도비",
    "CRM": "세일즈포스",
    "ORCL": "오라클",
    "ARM": "ARM",
    "ANET": "Arista Networks",
    "MPWR": "Monolithic Power",
    "MCHP": "Microchip",
    "ON": "ON Semi",
    "LSCC": "Lattice Semi",

    # 빅테크 / 플랫폼
    "AAPL": "애플",
    "MSFT": "마이크로소프트",
    "GOOGL": "알파벳A",
    "GOOG": "알파벳C",
    "META": "메타",
    "AMZN": "아마존",
    "TSLA": "테슬라",
    "NFLX": "넷플릭스",

    # 클라우드 / 데이터 / 사이버보안 / SW
    "SNOW": "Snowflake",
    "MDB": "MongoDB",
    "DDOG": "Datadog",
    "NET": "Cloudflare",
    "ZS": "Zscaler",
    "CRWD": "CrowdStrike",
    "PANW": "Palo Alto",
    "OKTA": "Okta",
    "NOW": "ServiceNow",
    "TEAM": "Atlassian",
    "SHOP": "Shopify",
    "U": "Unity",
    "DOCU": "DocuSign",
    "HUBS": "HubSpot",
    "RBLX": "Roblox",
    "TWLO": "Twilio",
    "SMAR": "Smartsheet",
    "ESTC": "Elastic",
    "APPF": "AppFolio",
    "AI": "C3.ai",

    # 코인/채굴/비트코인 노출
    "COIN": "코인베이스",
    "MSTR": "마이크로스트래티지",
    "RIOT": "Riot",
    "MARA": "마라톤디지털",
    "CLSK": "클린스파크",
    "BITF": "비트팜",

    # ETF / 레버리지
    "QQQ": "나스닥100",
    "SPY": "S&P500",
    "VOO": "S&P500 VOO",
    "TQQQ": "나스닥3배",
    "SQQQ": "나스닥인버스3배",
    "SOXL": "반도체3배",
    "SOXS": "반도체인버스3배",
    "TECL": "기술주3배",
    "SPXL": "S&P3배",
    "SPXS": "S&P인버스3배",
    "LABU": "바이오3배",
    "LABD": "바이오인버스3배",
    "ARKK": "ARKK",
    "IWM": "Russell 2000",

    # 소비/브랜드
    "MCD": "맥도날드",
    "SBUX": "스타벅스",
    "NKE": "나이키",
    "COST": "코스트코",
    "WMT": "월마트",
    "KO": "코카콜라",
    "PEP": "펩시",
    "CMG": "Chipotle",

    # 헬스케어
    "JNJ": "존슨앤존슨",
    "PFE": "화이자",
    "MRNA": "모더나",
    "UNH": "유나이티드헬스",
    "ABBV": "애브비",
    "MRK": "머크",
    "LLY": "Eli Lilly",
    "REGN": "Regeneron",

    # 금융
    "JPM": "JP모건",
    "BAC": "뱅크오브아메리카",
    "C": "씨티",
    "GS": "골드만삭스",
    "MS": "모건스탠리",
    "SCHW": "Charles Schwab",

    # 에너지/전력/데이터센터 인프라
    "XOM": "엑슨모빌",
    "CVX": "셰브론",
    "NEE": "NextEra Energy",
    "DUK": "Duke Energy",
    "SO": "Southern Co",
    "EXC": "Exelon",
    "EQIX": "Equinix(데이터센터 REIT)",
    "DLR": "Digital Realty",

    # 산업/기타
    "CAT": "캐터필러",
    "MMM": "3M",
    "HON": "허니웰",
    "LMT": "Lockheed Martin",

    # 통신/엔터
    "DIS": "디즈니",
    "VZ": "버라이즌",
    "T": "AT&T",
}

def normalize_symbol(user_input: str) -> str:
    """한글이면 티커로 변환, 아니면 공백 제거 후 대문자"""
    name = user_input.strip()
    if name in KOREAN_TICKER_MAP:
        return KOREAN_TICKER_MAP[name]
    return name.replace(" ", "").upper()


# -------------------------------
# FGI (CNN Fear & Greed Index)
# -------------------------------
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


# -------------------------------
# USD/KRW 환율 조회
# -------------------------------
def get_usdkrw_rate():
    try:
        ticker = yf.Ticker("USDKRW=X")
        df = ticker.history(period="1d")
        if df.empty:
            return 1350.0
        return float(df["Close"].iloc[-1])
    except Exception:
        return 1350.0  # 실패 시 대략값


# -------------------------------
# 현재가(시외 포함 가능) 조회
# -------------------------------
def get_last_extended_price(symbol: str):
    """
    정규장 + 프리/애프터마켓까지 포함한
    가장 최근 1분봉 종가를 반환 (참고용)
    """
    try:
        t = yf.Ticker(symbol)
        df = t.history(period="1d", interval="1m", auto_adjust=False, prepost=True)
        if df.empty:
            return None
        return float(df["Close"].iloc[-1])
    except Exception:
        return None


# -------------------------------
# 모드별 설정
# -------------------------------
def get_mode_config(mode_name: str):
    if mode_name == "단타":
        return {"name": "단타", "period": "3mo", "take_profit_pct": 7, "stop_loss_pct": 10}
    elif mode_name == "장기":
        return {"name": "장기", "period": "1y", "take_profit_pct": 25, "stop_loss_pct": 30}
    else:  # 스윙
        return {"name": "스윙", "period": "6mo", "take_profit_pct": 12, "stop_loss_pct": 20}


# -------------------------------
# 가격 데이터
# -------------------------------
def get_price_data(symbol, period="6mo"):
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval="1d", auto_adjust=False)
    if df.empty:
        return df
    return df[["Open", "High", "Low", "Close", "Volume"]].dropna()


# -------------------------------
# 지표 계산 (볼밴 / MACD / 스토캐 / RSI / MA5/MA50)
# -------------------------------
def add_indicators(df):
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

    # 스캐너용 MA50
    df["MA50"] = close.rolling(50).mean()

    return df.dropna()


# -------------------------------
# 스캐너용: 데이터+지표 (캐시 + 예외 처리)
# -------------------------------
@st.cache_data(ttl=1800)
def load_price_for_scan(symbol: str, period: str = "6mo"):
    try:
        df = get_price_data(symbol, period)
    except YFRateLimitError:
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

    if df.empty or len(df) < 40:
        return pd.DataFrame()
    return add_indicators(df)


# -------------------------------
# 지표 코멘트들
# -------------------------------
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


# -------------------------------
# 단기 상/하방 코멘트
# -------------------------------
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


# -------------------------------
# 매매 신호 로직 (단일 종목 분석용)
# -------------------------------
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

    # 평단 없음 = 신규 진입 관점
    if avg_price <= 0:
        if fear and price < bbl * 1.02 and k < 30 and rsi < 45:
            return "초기 매수 관심 (공포 국면)"
        elif greed and price < bbl * 0.98 and k < 15 and rsi < 30:
            return "초기 매수 관심 (탐욕 중 저점)"
        elif strong_oversold:
            return "초기 매수 관심"
        else:
            return "관망 (신규 진입 관점)"

    # 기본 분할매수
    base_buy_cond = (strong_oversold and profit_pct > -stop_loss_pct)
    if fear and price < bbl * 1.02 and k < 30 and rsi < 45 and profit_pct > -stop_loss_pct * 1.2:
        return "분할매수 (공포 국면)"
    elif greed and price < bbl * 0.98 and k < 15 and rsi < 30 and profit_pct > -stop_loss_pct:
        return "분할매수"
    elif base_buy_cond:
        return "분할매수"

    # 합리적 물타기
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

    # 혼합형 매도
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


# -------------------------------
# 가격 레벨 계산
# -------------------------------
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

    # 매수 구간
    if price > ma20:
        buy_low = ma20 * 0.98
        buy_high = ma20 * 1.01
    else:
        buy_low = bbl * 0.98
        buy_high = bbl * 1.02

    # 매도 목표: 0 / 1 / 2차
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

    # 손절
    if avg_price > 0:
        mode_stop = avg_price * (1 - stop_loss_pct / 100)
    else:
        mode_stop = price * (1 - stop_loss_pct / 100)

    sl0 = mode_stop
    deep_candidate = min(recent_low * 0.99, bbl * 0.97)
    sl1 = min(sl0 * 0.97, deep_candidate)

    return buy_low, buy_high, tp0, tp1, tp2, sl0, sl1


# -------------------------------
# 스캐너 조건식들 (공격형)
# -------------------------------
def scan_trend_start(df: pd.DataFrame):
    """
    상승추세 시작 (공격형)
    """
    df = df.copy().dropna()
    if len(df) < 60:
        return False, ""

    recent = df.tail(20)
    last = recent.iloc[-1]
    price = last["Close"]
    ma20 = last["MA20"]
    ma50 = last["MA50"]
    rsi = last["RSI14"]

    if ma20 <= ma50:
        return False, ""

    past = recent.iloc[:-3]
    cross_mask = (past["MA20"].shift(1) <= past["MA50"].shift(1)) & (past["MA20"] > past["MA50"])
    if not cross_mask.tail(15).any():
        return False, ""

    if not (price > ma20 and 40 <= rsi <= 70):
        return False, ""

    last3 = recent.tail(3)
    pos_days = (last3["Close"] > last3["Open"]).sum()
    if pos_days < 2:
        return False, ""

    comment = "MA20>MA50 골든크로스 이후, 최근 3일 중 2일 이상 양봉으로 초기 상승 추세가 강화되는 구간입니다."
    return True, comment


def scan_momentum_spike(df: pd.DataFrame):
    """
    급등주 (공격형)
    """
    df = df.copy().dropna()
    if len(df) < 30:
        return False, ""

    recent = df.tail(6)
    last = recent.iloc[-1]
    prev = recent.iloc[-2]

    price = last["Close"]
    prev_close = prev["Close"]
    ret_1d = (price - prev_close) / prev_close * 100

    price_5ago = recent.iloc[0]["Close"]
    ret_5d = (price - price_5ago) / price_5ago * 100

    vol = df["Volume"]
    vol_now = last["Volume"]
    vol_avg20 = vol.tail(20).mean()
    rsi = last["RSI14"]

    cond_ret = (ret_1d >= 3) or (ret_5d >= 8)
    cond_vol = vol_now >= vol_avg20 * 1.3
    cond_rsi = rsi >= 55

    last3 = df.tail(3)
    up_days = (last3["Close"] > last3["Open"]).sum()
    cond_up = up_days >= 2

    if cond_ret and cond_vol and cond_rsi and cond_up:
        vol_ratio = vol_now / vol_avg20 if vol_avg20 > 0 else 1.0
        comment = (
            f"당일 {ret_1d:.1f}%, 5일 {ret_5d:.1f}% 상승, "
            f"거래량 {vol_ratio:.1f}배, 최근 3일 중 {up_days}일 상승한 모멘텀 급등 패턴입니다."
        )
        return True, comment
    return False, ""


def scan_reversal(df: pd.DataFrame):
    """
    추세 전환(바닥 반등) (공격형)
    """
    df = df.copy().dropna()
    if len(df) < 40:
        return False, ""

    recent = df.tail(20)
    last = recent.iloc[-1]

    rsi_series = recent["RSI14"]
    if rsi_series.min() > 30:
        return False, ""
    if last["RSI14"] < 40:
        return False, ""

    last3 = recent.tail(3)
    cond_close_up = (last3["Close"].diff() > 0).sum() >= 2
    cond_candle_up = (last3["Close"] > last3["Open"]).sum() >= 2
    if not (cond_close_up or cond_candle_up):
        return False, ""

    k = recent["STOCH_K"]
    d = recent["STOCH_D"]
    cross = (k.shift(1) < d.shift(1)) & (k > d)
    if not cross.tail(5).any():
        return False, ""

    prev = recent.iloc[-2]
    bbl = last["BBL"]
    cond_band = (prev["Close"] < bbl) and (last["Close"] > bbl * 0.99)
    if not cond_band:
        return False, ""

    comment = "과매도 후 RSI·스토캐스틱 회복, 하단 밴드 밖→안 재진입 + 최근 연속 상승으로 바닥 반등 가능성이 높은 구간입니다."
    return True, comment


def scan_pullback(df: pd.DataFrame):
    """
    눌림목 반등 (공격형)
    """
    df = df.copy().dropna()
    if len(df) < 50:
        return False, ""

    recent = df.tail(15)
    last = recent.iloc[-1]
    prev = recent.iloc[-2]

    ma20 = last["MA20"]
    ma50 = last["MA50"]
    if not (ma20 > ma50):
        return False, ""

    near_ma20 = (np.abs(recent["Close"] - recent["MA20"]) / recent["MA20"] * 100) <= 3
    if not near_ma20.any():
        return False, ""

    if last["Close"] <= prev["Close"]:
        return False, ""

    rsi = last["RSI14"]
    if not (35 <= rsi <= 65):
        return False, ""

    vol = df["Volume"]
    recent_vol = vol.tail(10)
    avg_vol = recent_vol.mean()
    min_vol = recent_vol.min()
    today_vol = last["Volume"]

    if not (today_vol >= avg_vol and min_vol <= avg_vol * 0.9):
        return False, ""

    comment = "중기 상승 추세에서 MA20 부근 눌림 후, 거래량 회복과 함께 다시 양봉 반등이 나오는 눌림목 재상승 패턴입니다."
    return True, comment


def chunk_list(lst, size):
    """리스트를 size개 단위로 잘라주는 유틸"""
    for i in range(0, len(lst), size):
        yield lst[i:i+size]


def run_multi_scanner(selected_scans):
    results = {
        "상승추세 초기": [],
        "급등주": [],
        "추세 전환": [],
        "눌림목 반등": [],
    }

    items = list(SCAN_UNIVERSE.items())
    batch_size = 40  # 40개씩 끊어서 처리

    for batch_idx, batch in enumerate(chunk_list(items, batch_size)):
        for symbol, name in batch:
            try:
                df = load_price_for_scan(symbol, period="6mo")
            except YFRateLimitError:
                # 레이트 리밋 걸리면 잠깐 쉬고 스킵
                time.sleep(3)
                continue
            except Exception:
                continue

            if df.empty:
                continue

            last = df.iloc[-1]
            price = float(last["Close"])
            prev_close = float(df.iloc[-2]["Close"])
            daily_ret = (price - prev_close) / prev_close * 100

            base_info = {
                "티커": symbol,
                "이름": name,
                "현재가": round(price, 2),
                "당일수익률(%)": round(daily_ret, 2),
            }

            if "상승추세 초기" in selected_scans:
                ok, comment = scan_trend_start(df)
                if ok:
                    entry = base_info.copy()
                    entry["코멘트"] = comment
                    results["상승추세 초기"].append(entry)

            if "급등주" in selected_scans:
                ok, comment = scan_momentum_spike(df)
                if ok:
                    entry = base_info.copy()
                    entry["코멘트"] = comment
                    results["급등주"].append(entry)

            if "추세 전환" in selected_scans:
                ok, comment = scan_reversal(df)
                if ok:
                    entry = base_info.copy()
                    entry["코멘트"] = comment
                    results["추세 전환"].append(entry)

            if "눌림목 반등" in selected_scans:
                ok, comment = scan_pullback(df)
                if ok:
                    entry = base_info.copy()
                    entry["코멘트"] = comment
                    results["눌림목 반등"].append(entry)

            # 각 심볼 사이 0.15초 대기 → 레이트 리밋 완화
            time.sleep(0.15)

        # 40개 배치마다 약간 더 쉬기
        time.sleep(0.5)

    return results


# -------------------------------
# 메인 앱
# -------------------------------
def main():
    st.set_page_config(page_title="내 주식 자동판단기 + 스캐너", page_icon="📈", layout="centered")

    if "recent_symbols" not in st.session_state:
        st.session_state["recent_symbols"] = []

    st.title("📈 내 주식 자동판단기 + 📊 종목 스캐너")

    mode = st.radio("모드 선택", ["내 종목 분석", "종목 스캐너"], horizontal=True)

    # ==========================
    # 1) 내 종목 분석 모드
    # ==========================
    if mode == "내 종목 분석":
        st.write("단타 · 스윙 · 장기 + FGI + 기술적 지표 기반으로 매수/매도/물타기/신규진입 구간을 정리해줍니다.")
        st.caption("※ 종목 입력은 영어 티커가 가장 정확합니다. 한글 이름은 일부 인기 종목만 자동 인식됩니다.")

        col1, col2 = st.columns(2)
        with col1:
            user_symbol = st.text_input(
                "종목 이름/티커 (예: NVDA, 엔비디아, META, TQQQ)",
                value="엔비디아",
            )
            holding_type = st.radio("보유 상태", ["보유 중", "신규 진입 검토"], horizontal=True)
        with col2:
            mode_name = st.selectbox("투자 모드 선택", ["단타", "스윙", "장기"], index=1)

        prefix = user_symbol.strip().upper().replace(" ", "")
        candidates = sorted(set(POPULAR_SYMBOLS + st.session_state["recent_symbols"]))
        suggestions = []
        if prefix:
            suggestions = [s for s in candidates if s.startswith(prefix)]
        if suggestions:
            st.caption("자동완성 도움: " + ", ".join(suggestions[:6]))

        col3, col4 = st.columns(2)
        avg_price = 0.0
        shares = 0
        if holding_type == "보유 중":
            with col3:
                avg_price = st.number_input("내 평단가 (USD)", min_value=0.0, value=0.0, step=0.01)
            with col4:
                shares = st.number_input("보유 수량 (주)", min_value=0, value=0, step=1)

        run = st.button("🚀 분석하기")

        if not run:
            return

        symbol = normalize_symbol(user_symbol)
        display_name = user_symbol
        cfg = get_mode_config(mode_name)

        with st.spinner("데이터 불러오는 중..."):
            fgi = fetch_fgi()
            df = get_price_data(symbol, cfg["period"])

            if df.empty:
                st.error("❌ 이 종목은 선택한 기간 동안 데이터가 부족합니다. 다른 모드(스윙/장기) 또는 티커를 확인해 주세요.")
                return

            df = add_indicators(df)
            if df.empty:
                st.error("❌ 지표 계산에 필요한 데이터가 부족합니다. 다른 기간/모드로 다시 시도해 주세요.")
                return

            last = df.iloc[-1]

        # 최근 시외 포함 가격
        ext_price = get_last_extended_price(symbol)

        # 최근 검색 목록 업데이트
        if symbol not in st.session_state["recent_symbols"]:
            st.session_state["recent_symbols"].append(symbol)
            st.session_state["recent_symbols"] = st.session_state["recent_symbols"][-30:]

        price = float(last["Close"])  # 정규장 종가
        profit_pct = (price - avg_price) / avg_price * 100 if avg_price > 0 else 0.0
        total_pnl = (price - avg_price) * shares if (shares > 0 and avg_price > 0) else 0.0

        eff_avg_price = avg_price if holding_type == "보유 중" else 0.0
        signal = make_signal(last, eff_avg_price, cfg, fgi)
        buy_low, buy_high, tp0, tp1, tp2, sl0, sl1 = calc_levels(df, last, eff_avg_price, cfg)
        bias_comment = short_term_bias(last)

        near_buy_zone = (price >= buy_low * 0.97 and price <= buy_high * 1.03)
        near_sell_zone = (price >= tp0 * 0.97 and price <= tp2 * 1.05)
        near_stop_zone = (price <= sl0 * 1.03)

        context = ""
        if near_stop_zone and holding_type == "보유 중":
            context = " (손절/리스크 관리 구간에 접근 중입니다)"
        elif near_sell_zone and holding_type == "보유 중":
            context = " (곧 매도/익절 추천 가격대에 도달합니다)"
        elif near_buy_zone and holding_type == "보유 중" and profit_pct <= 0:
            context = " (곧 물타기/추가 매수 가격대에 도달합니다)"
        elif near_buy_zone and holding_type == "신규 진입 검토":
            context = " (신규 진입/분할 매수 구간에 가깝습니다)"

        st.subheader("🧾 요약")
        st.write(f"- 입력 종목: **{display_name}** → 실제 티커: **{symbol}**")
        if fgi is not None:
            st.write(f"- 공포·탐욕지수(FGI, CNN): **{fgi:.1f}**")
        else:
            st.write("- 공포·탐욕지수(FGI): 조회 실패 → 시장심리는 제외하고 지표만 사용")

        st.subheader("💼 보유/신규 상태")
        st.write(f"- 정규장 기준 현재가(종가): **{price:.2f} USD**")
        if ext_price is not None:
            diff_pct = (ext_price - price) / price * 100
            sign = "+" if diff_pct >= 0 else ""
            st.write(
                f"- 최근 가격 (시외 포함 가능): **{ext_price:.2f} USD** "
                f"(정규장 종가 대비 {sign}{diff_pct:.2f}%)"
            )

        st.write(f"- 투자 모드: **{cfg['name']}** (기간: {cfg['period']}, 익절: +{cfg['take_profit_pct']}%, 손절: -{cfg['stop_loss_pct']}%)")
        st.write(f"- 보유 상태: **{holding_type}**")

        if holding_type == "보유 중":
            if avg_price > 0:
                st.write(f"- 평단가: **{avg_price:.2f} USD**")
                st.write(f"- 수익률: **{profit_pct:.2f}%** (정규장 기준)")
            else:
                st.write("- 평단가: 입력 안 함")
                st.write("- 수익률: 평단이 없어 계산 불가")
            if shares > 0 and avg_price > 0:
                rate = get_usdkrw_rate()
                pnl_krw = total_pnl * rate
                st.write(f"- 보유 수량: **{shares} 주**")
                st.write(f"- 평가손익: **{total_pnl:,.2f} USD** (약 **{pnl_krw:,.0f} KRW**, 환율 {rate:,.2f}원 기준)")
        else:
            st.write("- 현재는 보유 중이 아니라, 신규 진입 시점만 검토합니다.")

        st.subheader("🎯 매매 판단")
        st.write(f"**추천 액션:** ⭐ {signal}{context} ⭐")
        st.write(f"**단기 방향성 코멘트:** {bias_comment}")

        st.subheader("📌 기술적 기준 가격 레벨 (참고용)")
        st.write(f"- 매수/추가매수 구간: **{buy_low:.2f} ~ {buy_high:.2f} USD**")

        if holding_type == "보유 중":
            st.write(f"- 0차 매도 추천가 (선행 익절): **{tp0:.2f} USD**")
            st.write(f"- 1차 매도 추천가: **{tp1:.2f} USD**")
            st.write(f"- 2차 매도 추천가: **{tp2:.2f} USD**")
            st.write(f"- 0차 손절가 (경고 손절): **{sl0:.2f} USD**")
            st.write(f"- 1차 손절가 (최종 방어선): **{sl1:.2f} USD**")
        else:
            entry1 = min(buy_high, buy_low * 1.03)
            entry2 = buy_low
            st.write(f"- 1차 진입(소량 매수) 추천가: **{entry1:.2f} USD** 근처")
            st.write(f"- 2차 분할매수(조정 시): **{entry2:.2f} USD** 이하 구간")
            st.caption("※ 신규 진입은 한 번에 몰입하기보다, 1차·2차로 나누어 분할 매수하는 것을 전제로 한 가이드입니다.")

        st.subheader("📊 지표 상태 (마지막 일봉 기준)")
        rsi = float(last["RSI14"])
        k = float(last["STOCH_K"])
        d = float(last["STOCH_D"])
        macd = float(last["MACD"])
        macds = float(last["MACD_SIGNAL"])
        bbl = float(last["BBL"])
        bbu = float(last["BBU"])
        ma20 = float(last["MA20"])

        st.write(f"- 20일선(MA20): **{ma20:.2f}**  ({'강세' if price > ma20 else '약세/조정'})")
        st.write(f"- 볼린저 하단(BBL): **{bbl:.2f}**, 상단(BBU): **{bbu:.2f}**  ({comment_bb(price, bbl, bbu, ma20)})")
        st.write(f"- 스토캐스틱 K: **{k:.2f}**, D: **{d:.2f}**  ({comment_stoch(k, d)})")
        st.write(f"- MACD: **{macd:.4f}**, Signal: **{macds:.4f}**  ({comment_macd(macd, macds)})")
        st.write(f"- RSI(14): **{rsi:.2f}**  ({comment_rsi(rsi)})")

        st.subheader("📈 가격 / 밴드 차트 (최근 약 6개월)")
        chart_df = df[["Close", "MA20", "BBL", "BBU"]].tail(120)
        st.line_chart(chart_df)

    # ==========================
    # 2) 종목 스캐너 모드
    # ==========================
    else:
        st.write("인기 종목/ETF + AI/클라우드/데이터센터/러셀2000 일부를 대상으로, 상승 추세 시작 / 급등 / 추세 전환 / 눌림목 반등 패턴을 자동으로 찾아줍니다.")
        scan_options = ["상승추세 초기", "급등주", "추세 전환", "눌림목 반등"]
        selected = st.multiselect(
            "찾고 싶은 패턴 선택 (복수 선택 가능)",
            scan_options,
            default=scan_options
        )

        run_scan = st.button("🚀 스캔 실행")

        if not run_scan:
            return

        if not selected:
            st.warning("적어도 하나 이상의 패턴을 선택해 주세요.")
            return

        with st.spinner("인기 종목 리스트를 스캔 중입니다..."):
            results = run_multi_scanner(selected)

        st.subheader("📊 스캔 결과")

        for key in selected:
            items = results.get(key, [])
            st.markdown(f"#### 🔍 {key}")
            if not items:
                st.write("- 해당 조건에 맞는 종목이 없습니다.")
                continue
            df_show = pd.DataFrame(items)
            st.dataframe(df_show, use_container_width=True)


if __name__ == "__main__":
    main()
