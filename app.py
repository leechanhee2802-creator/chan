import streamlit as st
import yfinance as yf
import pandas as pd
import requests

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


# ===== 미국 시장 실시간 흐름 관련 =====
def safe_last_change_info(ticker_str: str):
    """
    yfinance.Ticker.info 를 이용해
    - regularMarketPrice
    - regularMarketPreviousClose
    기준으로 전일 대비 변동률을 계산
    선물, 금리, DXY 등에 공통 사용
    """
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
    """
    QQQ / VOO / SOXX 에 대해
    - PRE 이면 preMarketPrice
    - POST 이면 postMarketPrice
    - 나머지는 regularMarketPrice
    를 현재가로 사용하고, 전일 종가 대비 % 계산.
    """
    try:
        t = yf.Ticker(symbol)
        info = t.info

        market_state = info.get("marketState", "")
        prev_close = info.get("regularMarketPreviousClose")

        pre = info.get("preMarketPrice")
        post = info.get("postMarketPrice")
        regular = info.get("regularMarketPrice")

        if market_state == "PRE" and pre is not None:
            current = pre
            basis = "프리장 기준"
        elif market_state == "POST" and post is not None:
            current = post
            basis = "애프터장 기준"
        elif regular is not None:
            current = regular
            basis = "정규장 기준"
        else:
            current = pre or post or regular
            basis = "기준 불명"

        chg_pct = None
        if current is not None and prev_close not in (None, 0, 0.0):
            chg_pct = (current - prev_close) / prev_close * 100

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
    """
    미국 지수선물, 금리, 달러, ETF(QQQ/VOO/SOXX), FGI 를 한 번에 묶어서 반환
    - 선물/금리/DXY: 전일 종가 대비 %
    - ETF: 프리/정규/애프터 자동 선택 + 전일 종가 대비 %
    """
    overview = {}

    # 선물 (나스닥 / S&P500)
    nq_last, nq_chg, nq_state = safe_last_change_info("NQ=F")
    es_last, es_chg, es_state = safe_last_change_info("ES=F")

    overview["futures"] = {
        "nasdaq": {
            "last": nq_last,
            "chg_pct": nq_chg,
            "state": nq_state,
        },
        "sp500": {
            "last": es_last,
            "chg_pct": es_chg,
            "state": es_state,
        },
    }

    # 10년물 금리 (^TNX: 1/10 단위)
    tnx_last, tnx_chg, tnx_state = safe_last_change_info("^TNX")
    if tnx_last is not None:
        us10y = tnx_last / 10.0
        us10y_chg = tnx_chg / 10.0 if tnx_chg is not None else None
    else:
        us10y, us10y_chg = None, None

    # 달러 인덱스
    dxy_last, dxy_chg, dxy_state = safe_last_change_info("DX-Y.NYB")

    overview["rates_fx"] = {
        "us10y": us10y,
        "us10y_chg": us10y_chg,
        "us10y_state": tnx_state,
        "dxy": dxy_last,
        "dxy_chg": dxy_chg,
        "dxy_state": dxy_state,
    }

    # ETF 3개 (QQQ / VOO / SOXX)
    etfs = []
    etfs.append(get_etf_price_with_prepost("QQQ", "QQQ (나스닥100 ETF)"))
    etfs.append(get_etf_price_with_prepost("VOO", "VOO (S&P500 ETF)"))
    etfs.append(get_etf_price_with_prepost("SOXX", "SOXX (반도체 ETF)"))

    overview["etfs"] = etfs

    # FGI
    overview["fgi"] = fetch_fgi()

    return overview


def compute_market_score(overview: dict):
    """
    선물 + 금리 + 달러 + ETF 3개를 점수화
    대략 점수 범위: -8 ~ +8
    """
    if not overview:
        return 0, "데이터 부족", "실시간 시장 데이터를 불러오지 못했습니다."

    fut = overview.get("futures", {})
    rf = overview.get("rates_fx", {})
    etfs = overview.get("etfs", [])

    score = 0
    details = []

    # 나스닥 선물
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

    # 10년물 금리
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

    # 달러 인덱스
    dxy = rf.get("dxy")
    if dxy is not None:
        if dxy < 104:
            score += 1
            details.append(f"DXY {dxy:.2f} (달러 약세 → Risk-on 우호)")
        elif dxy > 106:
            score -= 1
            details.append(f"DXY {dxy:.2f} (달러 강세 → Risk-off 경계)")

    # ETF 3종 (QQQ / VOO / SOXX)
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


# -------------------------------
# 모드별 설정 (단타/스윙/장기)
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

    df["MA50"] = close.rolling(50).mean()

    return df.dropna()


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
# 메인 앱
# -------------------------------
def main():
    st.set_page_config(page_title="내 주식 자동판단기 + 시장 개요", page_icon="📈", layout="centered")

    if "recent_symbols" not in st.session_state:
        st.session_state["recent_symbols"] = []

    st.title("📈 내 주식 자동판단기")
    st.caption("위에는 미국 시장 개요(선물/금리/달러/ETF), 아래는 개별 종목 판독기")

    # ===== 시장 개요: 보조지표 박스 =====
    with st.expander("🌍 미국 시장 실시간 흐름 (보조지표)", expanded=True):
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            refresh = st.button("🔄 새로고침", key="refresh_overview", help="캐시를 비우고 최신 데이터로 다시 불러옵니다.")
        if refresh:
            get_us_market_overview.clear()

        with st.spinner("미국 선물 · 금리 · 달러 · ETF 상황 불러오는 중..."):
            ov = get_us_market_overview()

        score, label, detail_text = compute_market_score(ov)

        fut = ov.get("futures", {})
        rf = ov.get("rates_fx", {})
        etfs = ov.get("etfs", [])
        fgi_overview = ov.get("fgi")

        col1, col2, col3 = st.columns(3)

        # 나스닥 선물
        nas = fut.get("nasdaq", {})
        with col1:
            last = nas.get("last")
            chg = nas.get("chg_pct")
            state = nas.get("state", "")
            title = "NQ=F"
            if state:
                title += f" [{state}]"
            if last is not None and chg is not None:
                st.metric(title, f"{last:.1f}", f"{chg:.2f}%")
            else:
                st.metric(title, "N/A", "-")

        # S&P 선물
        es = fut.get("sp500", {})
        with col2:
            last = es.get("last")
            chg = es.get("chg_pct")
            state = es.get("state", "")
            title = "ES=F"
            if state:
                title += f" [{state}]"
            if last is not None and chg is not None:
                st.metric(title, f"{last:.1f}", f"{chg:.2f}%")
            else:
                st.metric(title, "N/A", "-")

        # 시장 종합 점수
        with col3:
            max_score = 8
            min_score = -8
            st.metric("시장 점수", f"{score} / {max_score}", label)
            st.caption(f"(범위: {min_score} ~ {max_score} | 선물·금리·달러·ETF 기준)")

        if detail_text:
            st.caption("· " + detail_text)

        st.markdown("---")

        col4, col5, col6 = st.columns(3)

        # 금리
        with col4:
            us10y = rf.get("us10y")
            us10y_chg = rf.get("us10y_chg")
            if us10y is not None:
                delta = f"{us10y_chg:.3f}p" if us10y_chg is not None else ""
                st.metric("미 10년물", f"{us10y:.2f}%", delta)
            else:
                st.metric("미 10년물", "N/A", "")

        # 달러
        with col5:
            dxy = rf.get("dxy")
            dxy_chg = rf.get("dxy_chg")
            if dxy is not None and dxy_chg is not None:
                st.metric("DXY", f"{dxy:.2f}", f"{dxy_chg:.2f}%")
            else:
                st.metric("DXY", "N/A", "-")

        # FGI
        with col6:
            if fgi_overview is not None:
                st.metric("FGI", f"{fgi_overview:.1f}", "")
                if fgi_overview <= 25:
                    st.caption("극단적 공포")
                elif fgi_overview >= 75:
                    st.caption("극단적 탐욕")
            else:
                st.metric("FGI", "N/A", "")
                st.caption("CNN FGI 조회 실패")

        st.markdown("---")

        # ETF 3종
        st.caption("📈 ETF 3대장 (QQQ · VOO · SOXX) - PRE면 프리장, POST면 애프터장 기준")
        if etfs:
            cols_etf = st.columns(3)
            for i, e in enumerate(etfs):
                with cols_etf[i]:
                    sym = e.get("symbol")
                    name = e.get("name")
                    current = e.get("current")
                    basis = e.get("basis")
                    chg = e.get("chg_pct")
                    state = e.get("market_state", "")

                    # 제목: 심플하게 티커 + 상태만
                    title = sym
                    if state:
                        title += f" [{state}]"

                    # 값: 숫자만 (길이 줄이기)
                    if current is not None:
                        value_str = f"{current:.2f}"
                    else:
                        value_str = "N/A"

                    delta = f"{chg:.2f}%" if chg is not None else "-"

                    st.metric(title, value_str, delta)
                    # 아래에 작은 글씨로 풀네임 + 기준
                    st.caption(f"{name} · {basis}")

            st.caption("※ %는 항상 전일 종가 대비 기준입니다.")
        else:
            st.write("ETF 데이터를 불러오지 못했습니다.")

    st.markdown("---")  # 보조지표와 본 분석 섹션 시각적 분리

    # ===== 아래부터는 기존 "내 종목 판독기" =====
    st.subheader("🔍 내 종목 자동 판독기")

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

    # 자동완성 힌트
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


if __name__ == "__main__":
    main()
