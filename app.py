import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt

# ---- 한글 이름 → 티커 매핑 ----
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

    "엑슨모빌": "XOM", "셰브론": "CVX",
    "캐터필러": "CAT", "3M": "MMM",
    "허니웰": "HON", "디즈니": "DIS",
    "버라이즌": "VZ", "AT&T": "T",

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
    "ARKK": "ARKK", "아크": "ARKK", "아크K": "ARKK",
}

def normalize_symbol(user_input: str) -> str:
    name = user_input.strip()
    if name in KOREAN_TICKER_MAP:
        return KOREAN_TICKER_MAP[name]
    return name.replace(" ", "").upper()


# ---- FGI 자동 조회 ----
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


# ---- 모드 설정 ----
def get_mode_config(mode_name: str):
    # 초단타: 1개월, 예민 / 익절+3, 손절-5
    if mode_name == "초단타":
        return {"name": "초단타", "period": "1mo", "take_profit_pct": 3, "stop_loss_pct": 5}
    elif mode_name == "단타":
        return {"name": "단타", "period": "3mo", "take_profit_pct": 7, "stop_loss_pct": 10}
    elif mode_name == "장기":
        return {"name": "장기", "period": "1y", "take_profit_pct": 25, "stop_loss_pct": 30}
    else:  # 스윙
        return {"name": "스윙", "period": "6mo", "take_profit_pct": 12, "stop_loss_pct": 20}


# ---- 가격 데이터 ----
def get_price_data(symbol, period="6mo"):
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval="1d", auto_adjust=False)
    if df.empty:
        return df
    return df[["Open", "High", "Low", "Close", "Volume"]].dropna()


# ---- 지표 계산 ----
def add_indicators(df):
    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    std20 = close.rolling(20).std()
    df["MA20"] = ma20
    df["MA50"] = ma50
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
    roll_up = gain.ewm(alpha=1/14, adjust=False).mean()
    roll_down = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = roll_up / roll_down
    rsi = 100 - (100 / (1 + rs))
    df["RSI14"] = rsi

    return df.dropna()


# ---- 신호 로직 ----
def make_signal(row, avg_price, cfg, fgi=None):
    price = float(row["Close"])
    bbl   = float(row["BBL"])
    bbu   = float(row["BBU"])
    ma20  = float(row["MA20"])
    k     = float(row["STOCH_K"])
    d     = float(row["STOCH_D"])
    macd  = float(row["MACD"])
    macds = float(row["MACD_SIGNAL"])
    rsi   = float(row["RSI14"])

    take_profit_pct = cfg["take_profit_pct"]
    stop_loss_pct = cfg["stop_loss_pct"]

    if avg_price > 0:
        profit_pct = (price - avg_price) / avg_price * 100
    else:
        profit_pct = 0.0

    fear = (fgi is not None and fgi <= 25)
    greed = (fgi is not None and fgi >= 75)

    strong_overbought = (price > bbu and k > 80 and rsi > 65 and macd < macds)
    mild_overbought   = (price > ma20 and (k > 70 or rsi > 60))
    strong_oversold   = (price < bbl and k < 20 and d < 20 and rsi < 35)

    # 평단 없음
    if avg_price <= 0:
        if fear and price < bbl * 1.02 and k < 30 and rsi < 45:
            return "초기 매수 관심 (공포 국면)"
        elif greed and price < bbl * 0.98 and k < 15 and rsi < 30:
            return "초기 매수 관심 (탐욕 중 저점)"
        elif strong_oversold:
            return "초기 매수 관심"
        return "관망"

    # 기본 분할매수
    base_buy_cond = (strong_oversold and profit_pct > -stop_loss_pct)
    if fear and price < bbl * 1.02 and k < 30 and rsi < 45 and profit_pct > -stop_loss_pct * 1.2:
        return "분할매수 (공포 국면)"
    elif greed and price < bbl * 0.98 and k < 15 and rsi < 30 and profit_pct > -stop_loss_pct:
        return "분할매수"
    elif base_buy_cond:
        return "분할매수"

    # 합리적 물타기
    if avg_price > 0:
        loss_pct = -profit_pct
    else:
        loss_pct = 0.0
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


# ---- 가격 레벨 ----
def calc_levels(df, last, avg_price, cfg):
    recent = df.tail(20)
    recent_high = float(recent["Close"].max())
    recent_low = float(recent["Close"].min())

    price = float(last["Close"])
    ma20  = float(last["MA20"])
    bbl   = float(last["BBL"])
    bbu   = float(last["BBU"])

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

    # 추세 이탈 손절 라인 (최근 저점·MA20·BBL 조합)
    trend_stop = min(
        recent_low * 0.99,
        bbl * 0.99,
        ma20 * 0.97,
    )

    return buy_low, buy_high, tp0, tp1, tp2, sl0, sl1, trend_stop


# ---- 지표 상태 설명 ----
def describe_indicators(last):
    price = float(last["Close"])
    ma20 = float(last["MA20"])
    bbl = float(last["BBL"])
    bbu = float(last["BBU"])
    k = float(last["STOCH_K"])
    d = float(last["STOCH_D"])
    macd = float(last["MACD"])
    macds = float(last["MACD_SIGNAL"])
    rsi = float(last["RSI14"])

    desc = {}

    # MA20
    if price > ma20 * 1.02:
        desc["MA20"] = "단기 상승 추세 우위"
    elif price < ma20 * 0.98:
        desc["MA20"] = "단기 하락 추세 우위"
    else:
        desc["MA20"] = "단기 박스/중립"

    # 볼린저
    if price >= bbu * 0.99:
        desc["BB"] = "상단 근처 (과열/저항권)"
    elif price <= bbl * 1.01:
        desc["BB"] = "하단 근처 (저점권/지지권)"
    else:
        desc["BB"] = "밴드 중앙부 (중립)"

    # 스토캐
    if k > 80:
        desc["STOCH"] = "과열"
    elif k < 20:
        desc["STOCH"] = "과매도"
    else:
        desc["STOCH"] = "중립"

    # RSI
    if rsi >= 70:
        desc["RSI"] = "강한 과열"
    elif rsi >= 60:
        desc["RSI"] = "과열 주의"
    elif rsi <= 30:
        desc["RSI"] = "과매도"
    elif rsi <= 40:
        desc["RSI"] = "조정권"
    else:
        desc["RSI"] = "중립"

    # MACD
    if macd > 0 and macd > macds:
        desc["MACD"] = "상승 모멘텀 우위"
    elif macd < 0 and macd < macds:
        desc["MACD"] = "하락 모멘텀 우위"
    else:
        desc["MACD"] = "모멘텀 약/수렴"

    return desc


# ---- 초단타용 단기 모멘텀 판단 ----
def short_term_bias(df):
    # 최근 10거래일 기준
    recent = df.tail(10)
    close = recent["Close"]
    vol = recent["Volume"]

    if len(recent) < 5:
        return "데이터 부족", "데이터가 부족해서 단기 모멘텀 판단이 어렵습니다."

    # 5일 수익률
    ret_5 = (close.iloc[-1] - close.iloc[-5]) / close.iloc[-5] * 100

    ema5 = close.ewm(span=5, adjust=False).mean().iloc[-1]
    ema10 = close.ewm(span=10, adjust=False).mean().iloc[-1]

    vol_now = vol.iloc[-1]
    vol_avg = vol.mean()

    score = 0
    if ret_5 > 1:
        score += 1
    elif ret_5 < -1:
        score -= 1

    if ema5 > ema10:
        score += 1
    else:
        score -= 1

    if vol_now > vol_avg * 1.1:
        # 거래량이 평균보다 많으면 현재 방향 쪽으로 힘 실어줌
        score += np.sign(ret_5) if ret_5 != 0 else 0

    if score >= 2:
        bias = "상방 우세"
        detail = f"최근 5일 수익률 {ret_5:.2f}% 상승, 단기 이평(EMA5>EMA10), 거래량도 방향성에 힘을 실어주는 상태입니다."
    elif score <= -2:
        bias = "하방 우세"
        detail = f"최근 5일 수익률 {ret_5:.2f}% 하락, 단기 이평(EMA5<EMA10)과 거래량이 하락 쪽 모멘텀을 보여줍니다."
    else:
        bias = "중립"
        detail = f"최근 5일 수익률 {ret_5:.2f}%, 단기 이평과 거래량이 명확한 방향을 보여주지 않는 중립 구간입니다."

    return bias, detail


# ---- 메인 앱 ----
def main():
    st.set_page_config(page_title="내 주식 자동판단기", page_icon="📈", layout="wide")

    st.markdown(
        """
        <h1 style="margin-bottom:0;">📈 내 주식 자동판단기</h1>
        <p style="color:#666;margin-top:4px;">
        초단타 · 단타 · 스윙 · 장기 + FGI + 기술적 지표 기반으로
        매수 · 매도 · 물타기 · 손절 · 추세이탈을 한 번에 판단해주는 도구입니다.
        </p>
        <hr style="margin-top:0.5rem;margin-bottom:1rem;">
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.subheader("⚙️ 분석 설정")
        user_symbol = st.text_input("종목 이름/티커", value="엔비디아", help="예: 엔비디아, NVDA, 메타, TQQQ 등")
        mode_name = st.selectbox("투자 모드", ["초단타", "단타", "스윙", "장기"], index=2)
        avg_price = st.number_input("내 평단가 (USD)", min_value=0.0, value=0.0, step=0.01)
        shares = st.number_input("보유 수량 (주)", min_value=0, value=0, step=1)
        run = st.button("🔍 분석하기", use_container_width=True)

        st.markdown("---")
        st.caption("TIP: 종목 이름은 한글로 써도 티커로 자동 변환됩니다. (예: 엔비디아 → NVDA)")

    if not run:
        st.info("왼쪽 사이드바에서 종목과 평단을 입력하고 **🔍 분석하기** 버튼을 눌러주세요.")
        return

    symbol = normalize_symbol(user_symbol)
    cfg = get_mode_config(mode_name)

    with st.spinner("데이터 불러오는 중..."):
        fgi = fetch_fgi()
        df = get_price_data(symbol, cfg["period"])
        if df.empty:
            st.error("❌ 데이터를 불러오지 못했습니다. 티커(symbol)를 다시 확인해 주세요.")
            return
        df = add_indicators(df)
        last = df.iloc[-1]

    price = float(last["Close"])
    profit_pct = (price - avg_price) / avg_price * 100 if avg_price > 0 else 0.0
    total_pnl = (price - avg_price) * shares if (shares > 0 and avg_price > 0) else 0.0

    signal = make_signal(last, avg_price, cfg, fgi)
    buy_low, buy_high, tp0, tp1, tp2, sl0, sl1, trend_stop = calc_levels(df, last, avg_price, cfg)

    # 추세 이탈 손절 조건: 현재가가 추세 라인 아래
    if price <= trend_stop and avg_price > 0:
        signal = "추세 이탈 손절 고려"

    near_buy_zone = (price >= buy_low * 0.97 and price <= buy_high * 1.03)
    near_sell_zone = (price >= tp0 * 0.97 and price <= tp2 * 1.05)
    near_stop_zone = (price <= sl0 * 1.03)
    near_trend_stop = (price <= trend_stop * 1.02)

    context = ""
    if near_trend_stop:
        context = " (추세 이탈 구간에 접근 중입니다)"
    elif near_stop_zone:
        context = " (손절/리스크 관리 구간에 접근 중입니다)"
    elif near_sell_zone:
        context = " (곧 매도/익절 추천 가격대에 도달합니다)"
    elif near_buy_zone and profit_pct <= 0:
        context = " (곧 물타기/추가 매수 가격대에 도달합니다)"
    elif near_buy_zone and avg_price == 0:
        context = " (초기 진입 매수 구간에 가깝습니다)"

    desc = describe_indicators(last)
    bias, bias_detail = short_term_bias(df)

    # ===== 상단 요약 카드 =====
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("현재가", f"{price:.2f} USD")
    if avg_price > 0:
        col2.metric("평단가", f"{avg_price:.2f} USD")
        col3.metric("수익률", f"{profit_pct:.2f} %")
    else:
        col2.metric("평단가", "입력 없음")
        col3.metric("수익률", "계산 불가")
    if shares > 0 and avg_price > 0:
        col4.metric("평가손익", f"{total_pnl:,.2f} USD")
    else:
        col4.metric("평가손익", "-")

    st.markdown("### 🧾 요약")
    st.write(f"- 입력 종목: **{user_symbol}** → 실제 티커: **{symbol}**")
    if fgi is not None:
        st.write(f"- 공포·탐욕지수(FGI, CNN): **{fgi:.1f}**")
    else:
        st.write("- 공포·탐욕지수(FGI): 조회 실패 → 시장심리는 제외하고 지표만 사용")
    st.write(f"- 모드: **{cfg['name']}** (기간: {cfg['period']}, 익절: +{cfg['take_profit_pct']}%, 손절: -{cfg['stop_loss_pct']}%)")

    st.markdown("### 💼 보유 현황")
    st.write(f"- 현재가: **{price:.2f} USD**")
    if avg_price > 0:
        st.write(f"- 평단가: **{avg_price:.2f} USD**")
        st.write(f"- 수익률: **{profit_pct:.2f}%**")
    else:
        st.write("- 평단가: 입력 안 함")
        st.write("- 수익률: 평단이 없어 계산 불가")
    if shares > 0 and avg_price > 0:
        st.write(f"- 보유 수량: **{shares} 주**")
        st.write(f"- 평가손익: **{total_pnl:,.2f} USD**")

    st.markdown("### 🎯 매매 판단")
    st.write(f"**추천 액션:** ⭐ {signal}{context} ⭐")

    # 초단타 모드일 땐 단기 모멘텀 강조
    st.markdown("### ⚡ 단기 모멘텀 (초단타/단타 참고)")
    st.write(f"- 단기 방향성: **{bias}**")
    st.caption(bias_detail)

    st.markdown("### 📌 기술적 기준 가격 레벨 (참고용)")
    st.write(f"- 매수/추가매수 구간: **{buy_low:.2f} ~ {buy_high:.2f} USD**")
    st.write(f"- 0차 매도 추천가 (선행 익절): **{tp0:.2f} USD**")
    st.write(f"- 1차 매도 추천가: **{tp1:.2f} USD**")
    st.write(f"- 2차 매도 추천가: **{tp2:.2f} USD**")
    st.write(f"- 0차 손절가 (평단 기준 경고 손절): **{sl0:.2f} USD**")
    st.write(f"- 1차 손절가 (평단 기준 최종 방어선): **{sl1:.2f} USD**")
    st.write(f"- 추세 이탈 손절 라인 (평단과 무관한 추세 기준): **{trend_stop:.2f} USD**")

    st.markdown("### 📊 지표 상태 (마지막 일봉 기준)")
    st.write(f"- 20일선(MA20): **{last['MA20']:.2f}**  ({desc['MA20']})")
    st.write(f"- 볼린저 하단(BBL): **{last['BBL']:.2f}** / 상단(BBU): **{last['BBU']:.2f}**  ({desc['BB']})")
    st.write(f"- 스토캐스틱 K: **{last['STOCH_K']:.2f}**, D: **{last['STOCH_D']:.2f}**  ({desc['STOCH']})")
    st.write(f"- MACD: **{last['MACD']:.4f}**, Signal: **{last['MACD_SIGNAL']:.4f}**  ({desc['MACD']})")
    st.write(f"- RSI(14): **{last['RSI14']:.2f}**  ({desc['RSI']})")

    # ===== 차트 =====
    st.markdown("### 📉 가격 차트 (최근 60일)")

    chart_df = df.tail(60)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(chart_df.index, chart_df["Close"], label="Close", linewidth=1.5)
    ax.plot(chart_df.index, chart_df["MA20"], label="MA20", linestyle="--", linewidth=1)
    ax.fill_between(chart_df.index, chart_df["BBL"], chart_df["BBU"], alpha=0.1, label="Bollinger Band")

    ax.axhline(buy_low, linestyle="--", linewidth=0.8, label="매수구간 하단")
    ax.axhline(buy_high, linestyle="--", linewidth=0.8, label="매수구간 상단")
    ax.axhline(tp0, linestyle=":", linewidth=0.8, label="0차 매도가")
    ax.axhline(tp1, linestyle=":", linewidth=0.8, label="1차 매도가")
    ax.axhline(tp2, linestyle=":", linewidth=0.8, label="2차 매도가")
    ax.axhline(sl0, linestyle="-.", linewidth=0.8, label="0차 손절")
    ax.axhline(sl1, linestyle="-.", linewidth=0.8, label="1차 손절")
    ax.axhline(trend_stop, linestyle="-.", linewidth=1.0, label="추세 이탈 손절")

    ax.set_ylabel("Price (USD)")
    ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    st.pyplot(fig)


if __name__ == "__main__":
    main()
