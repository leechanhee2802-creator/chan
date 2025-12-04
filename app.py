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

    "코카콜라": "KO", "펩시": "PEP",
    "맥도날드": "MCD", "스타벅스": "SBUX",

    "QQQ": "QQQ", "SPY": "SPY", "VOO": "VOO",
    "TQQQ": "TQQQ", "SQQQ": "SQQQ",
    "SOXL": "SOXL", "SOXS": "SOXS",
    "TECL": "TECL", "SPXL": "SPXL", "SPXS": "SPXS",
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
    except:
        return None


# ---- 모드 설정 ----
def get_mode_config(mode_name: str):
    if mode_name == "초단타":
        return {"name": "초단타", "period": "1mo", "take_profit_pct": 3, "stop_loss_pct": 5}
    elif mode_name == "단타":
        return {"name": "단타", "period": "3mo", "take_profit_pct": 7, "stop_loss_pct": 10}
    elif mode_name == "장기":
        return {"name": "장기", "period": "1y", "take_profit_pct": 25, "stop_loss_pct": 30}
    else:
        return {"name": "스윙", "period": "6mo", "take_profit_pct": 12, "stop_loss_pct": 20}


# ---- 가격 데이터 (초단타 오류 방지 1mo → 2mo 자동 보정 포함) ----
def get_price_data(symbol, period="6mo"):
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval="1d", auto_adjust=False)

    # 🔥 1mo 데이터가 비어 있는 경우 → 자동으로 2mo로 재요청
    if df.empty:
        fallback_period = "2mo" if period == "1mo" else period
        df = ticker.history(period=fallback_period, interval="1d", auto_adjust=False)

    if df.empty:
        return df

    return df[["Open", "High", "Low", "Close", "Volume"]].dropna()


# ---- 지표 계산 ----
def add_indicators(df):
    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    df["MA20"] = close.rolling(20).mean()
    df["MA50"] = close.rolling(50).mean()

    std20 = close.rolling(20).std()
    df["BBL"] = df["MA20"] - 2 * std20
    df["BBU"] = df["MA20"] + 2 * std20

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
    rs = gain.ewm(alpha=1/14, adjust=False).mean() / loss.ewm(alpha=1/14, adjust=False).mean()
    df["RSI14"] = 100 - (100 / (1 + rs))

    return df.dropna()


# -------------------------------------------
#         🔥 초단타 고급 필터 강화 판정
# -------------------------------------------
def short_term_bias(df):
    recent = df.tail(10)
    close = recent["Close"]
    vol = recent["Volume"]

    if len(recent) < 5:
        return "데이터 부족", "초단타 분석에 필요한 데이터가 부족합니다."

    # 기본 지표
    ret_5 = (close.iloc[-1] - close.iloc[-5]) / close.iloc[-5] * 100
    ema5 = close.ewm(span=5, adjust=False).mean().iloc[-1]
    ema10 = close.ewm(span=10, adjust=False).mean().iloc[-1]
    vol_now = vol.iloc[-1]
    vol_avg = vol.mean()

    # 갭 체크
    prev_close = close.iloc[-2]
    today_open = recent["Open"].iloc[-1]
    gap_pct = (today_open - prev_close) / prev_close * 100

    # 변동성 체크 (High-Low)
    vola = (recent["High"] - recent["Low"]).mean()

    score = 0

    # 5일 수익률
    if ret_5 > 1.2:
        score += 1
    elif ret_5 < -1.2:
        score -= 1

    # 5-10EMA 추세
    if ema5 > ema10:
        score += 1
    else:
        score -= 1

    # 거래량 스파이크
    if vol_now > vol_avg * 1.3:
        score += np.sign(ret_5) if ret_5 != 0 else 0

    # 갭 상승/하락
    if gap_pct > 1:
        score += 1
    elif gap_pct < -1:
        score -= 1

    # 변동성 폭등
    if vola > recent["Close"].mean() * 0.015:
        score += np.sign(ret_5)

    # 결과 분류
    if score >= 3:
        return "상방 우세", f"EMA5>EMA10, 거래량↑, 변동성↑, 갭 상승 등 다수 지표가 단기 상승을 지지합니다. (score={score})"
    elif score <= -3:
        return "하방 우세", f"단기 이평 역전, 거래량/변동성 등이 하락 모멘텀을 나타냅니다. (score={score})"
    else:
        return "중립", f"상승·하락 신호 혼재. 명확한 방향성 없음. (score={score})"


# -------------------------------------------
#      🔥 신호 생성 + 물타기 + 매도 + 손절
# -------------------------------------------
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
        profit_pct = 0

    fear = (fgi is not None and fgi <= 25)
    greed = (fgi is not None and fgi >= 75)

    strong_overbought = (price > bbu and k > 80 and rsi > 65 and macd < macds)
    mild_overbought = (price > ma20 and (k > 70 or rsi > 60))
    strong_oversold = (price < bbl and k < 20 and d < 20 and rsi < 35)

    # 평단 없음 → 초기 매수 판단
    if avg_price <= 0:
        if strong_oversold or (fear and rsi < 40):
            return "초기 매수 관심"
        return "관망"

    # 합리적 물타기 조건
    loss_pct = -profit_pct
    oversold_signals = sum([
        rsi < 30,
        k < 20 and d < 20,
        price < bbl * 1.02,
        macd > macds
    ])

    if (stop_loss_pct <= loss_pct <= stop_loss_pct + 10) and oversold_signals >= 2:
        return "합리적 물타기 분할매수"

    # 익절 영역
    if profit_pct >= take_profit_pct:
        if strong_overbought or greed:
            return "강한 부분매도 (수익+과열)"
        return "부분매도 (수익 목표 도달)"

    # 과열 위험
    if strong_overbought:
        return "위험주의 (지표 과열)"

    # 손절 영역
    if profit_pct <= -stop_loss_pct:
        return "손절 or 비중축소 고려"

    return "관망"


# -------------------------------------------
#      🔥 레벨 계산 (매수/매도/손절)
# -------------------------------------------
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

    # 매도 레벨
    tp0 = price * (1 + 0.6 * take_profit_pct / 100)
    tp1 = price * (1 + take_profit_pct / 100)
    tp2 = price * (1 + 1.8 * take_profit_pct / 100)

    # 손절
    sl0 = price * (1 - stop_loss_pct / 100)
    sl1 = sl0 * 0.97

    # 추세 손절 (평단 무시)
    trend_stop = min(
        recent_low * 0.99,
        bbl * 0.99,
        ma20 * 0.97,
    )

    return buy_low, buy_high, tp0, tp1, tp2, sl0, sl1, trend_stop


# -------------------------------------------
#      🔥 지표 해석 문구
# -------------------------------------------
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

    desc["MA20"] = "단기 상승" if price > ma20 * 1.02 else ("단기 하락" if price < ma20 * 0.98 else "중립")
    desc["BB"] = (
        "상단 근처 (과열)" if price >= bbu * 0.99 else
        "하단 근처 (저점 가능)" if price <= bbl * 1.01 else
        "중앙부 (중립)"
    )
    desc["STOCH"] = "과열" if k > 80 else ("과매도" if k < 20 else "중립")
    desc["RSI"] = (
        "강한 과열" if rsi >= 70 else
        "과열 주의" if rsi >= 60 else
        "과매도" if rsi <= 30 else
        "조정권" if rsi <= 40 else
        "중립"
    )
    desc["MACD"] = (
        "상승 모멘텀" if macd > macds else
        "하락 모멘텀" if macd < macds else
        "약/수렴"
    )

    return desc


# -------------------------------------------
#             🔥 Streamlit 메인
# -------------------------------------------
def main():
    st.set_page_config(page_title="내 주식 자동판단기", page_icon="📈", layout="wide")

    st.markdown(
        """
        <h1>📈 내 주식 자동판단기</h1>
        <p style='color:#666'>초단타 · 단타 · 스윙 · 장기 + FGI + 기술적 지표 기반 자동 분석</p>
        <hr>
        """,
        unsafe_allow_html=True,
    )

    # ---- 사이드바 ----
    with st.sidebar:
        st.subheader("⚙️ 분석 설정")
        user_symbol = st.text_input("종목 이름/티커", value="엔비디아")
        mode_name = st.selectbox("투자 모드", ["초단타", "단타", "스윙", "장기"], index=2)
        avg_price = st.number_input("내 평단가(USD)", min_value=0.0, value=0.0)
        shares = st.number_input("보유 수량", min_value=0, value=0)
        run = st.button("🔍 분석하기", use_container_width=True)

    if not run:
        st.info("왼쪽에서 종목·평단을 입력하고 분석하기를 눌러주세요.")
        return

    symbol = normalize_symbol(user_symbol)
    cfg = get_mode_config(mode_name)

    # ---- 데이터 로딩 ----
    with st.spinner("데이터 불러오는 중..."):
        fgi = fetch_fgi()
        df = get_price_data(symbol, cfg["period"])

        if df.empty:
            st.error("❌ 데이터를 불러오지 못했습니다.")
            return

        df = add_indicators(df)
        last = df.iloc[-1]

    price = float(last["Close"])
    profit_pct = (price - avg_price) / avg_price * 100 if avg_price > 0 else 0
    total_pnl = (price - avg_price) * shares if (shares > 0 and avg_price > 0) else 0

    # ---- 신호 ----
    signal = make_signal(last, avg_price, cfg, fgi)
    buy_low, buy_high, tp0, tp1, tp2, sl0, sl1, trend_stop = calc_levels(df, last, avg_price, cfg)

    # 추세 이탈 추가 조건
    if price <= trend_stop and avg_price > 0:
        signal = "추세 이탈 손절 고려"

    near = ""
    if price <= trend_stop * 1.02:
        near = " (추세 이탈 구간 접근)"
    elif price <= sl0 * 1.03:
        near = " (손절 구간 접근)"
    elif price >= tp0 * 0.97:
        near = " (익절 구간 접근)"
    elif price >= buy_low * 0.97 and price <= buy_high * 1.03:
        near = " (매수/물타기 접근)"

    desc = describe_indicators(last)

    # 초단타 모멘텀
    bias, bias_detail = short_term_bias(df)

    # ---- 요약 카드 ----
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("현재가", f"{price:.2f}")
    col2.metric("평단", f"{avg_price:.2f}" if avg_price > 0 else "-")
    col3.metric("수익률", f"{profit_pct:.2f}%" if avg_price > 0 else "-")
    col4.metric("평가손익", f"{total_pnl:,.2f}" if avg_price > 0 else "-")

    st.markdown("### 🧾 종합 판단")
    st.write(f"**추천 액션:** ⭐ {signal}{near} ⭐")

    st.markdown("### ⚡ 초단타 모멘텀 (초단타/단타 모드 참고)")
    st.write(f"- 단기 방향성: **{bias}**")
    st.caption(bias_detail)

    st.markdown("### 🎯 가격 레벨")
    st.write(f"- 매수/추가매수: **{buy_low:.2f} ~ {buy_high:.2f}**")
    st.write(f"- 0차 매도: **{tp0:.2f}**")
    st.write(f"- 1차 매도: **{tp1:.2f}**")
    st.write(f"- 2차 매도: **{tp2:.2f}**")
    st.write(f"- 0차 손절: **{sl0:.2f}**")
    st.write(f"- 1차 손절: **{sl1:.2f}**")
    st.write(f"- 추세 손절: **{trend_stop:.2f}**")

    st.markdown("### 📊 지표 상태")
    st.write(f"- MA20: {last['MA20']:.2f} ({desc['MA20']})")
    st.write(f"- 볼린저: BBL={last['BBL']:.2f}, BBU={last['BBU']:.2f} ({desc['BB']})")
    st.write(f"- STOCH K={last['STOCH_K']:.2f}, D={last['STOCH_D']:.2f} ({desc['STOCH']})")
    st.write(f"- MACD={last['MACD']:.4f}, Signal={last['MACD_SIGNAL']:.4f} ({desc['MACD']})")
    st.write(f"- RSI14={last['RSI14']:.2f} ({desc['RSI']})")

    # ---- 가격 차트 ----
    st.markdown("### 📈 가격 차트 (60일)")
    chart = df.tail(60)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(chart.index, chart["Close"], label="Close", linewidth=1.5)
    ax.plot(chart.index, chart["MA20"], label="MA20", linestyle="--", linewidth=1)
    ax.fill_between(chart.index, chart["BBL"], chart["BBU"], alpha=0.15)

    ax.axhline(buy_low, linestyle="--", alpha=0.5)
    ax.axhline(buy_high, linestyle="--", alpha=0.5)
    ax.axhline(tp0, linestyle=":", alpha=0.5)
    ax.axhline(tp1, linestyle=":", alpha=0.5)
    ax.axhline(tp2, linestyle=":", alpha=0.5)
    ax.axhline(sl0, linestyle="-.", alpha=0.5)
    ax.axhline(sl1, linestyle="-.", alpha=0.5)
    ax.axhline(trend_stop, linestyle="-.", alpha=0.5, linewidth=1)

    ax.set_ylabel("Price")
    ax.legend(fontsize=8)
    st.pyplot(fig)


if __name__ == "__main__":
    main()
