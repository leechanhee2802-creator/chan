import numpy as np
import pandas as pd


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
