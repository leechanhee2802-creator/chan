"""Analysis utilities for indicators, states, and scanners."""

import numpy as np
import pandas as pd
import yfinance as yf

from app_core.market import compute_market_score, get_us_market_overview
from app_core.symbols import SCAN_CANDIDATES


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
    """
    ✅ 레벨 계산은 일봉 기반
    """
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
        sl0 = box_low * 0.985
        sl1 = box_low * 0.96
        return sl0, sl1

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


def calc_levels(df, last, cfg):
    """
    ✅ 레벨 계산은 일봉 기반
    """
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


def compute_state_and_action(
    holding_type: str,
    price_now: float,
    avg_price: float,
    levels: dict,
    last_row: pd.Series
):
    buy_low = levels.get("buy_low")
    buy_high = levels.get("buy_high")
    tp0 = levels.get("tp0")
    tp1 = levels.get("tp1")
    tp2 = levels.get("tp2")
    sl0 = levels.get("sl0")
    sl1 = levels.get("sl1")

    try:
        ma20 = float(last_row.get("MA20", np.nan))
    except Exception:
        ma20 = np.nan
    recover_candidates = []
    if buy_high is not None:
        recover_candidates.append(float(buy_high) * 1.005)
    if not np.isnan(ma20):
        recover_candidates.append(float(ma20) * 1.01)
    recover_level = max(recover_candidates) if recover_candidates else None

    structure_broken = False
    if price_now is not None and sl1 is not None:
        if price_now < float(sl1) * 0.998:
            structure_broken = True

    if structure_broken:
        if recover_level is not None:
            return (
                "구조 붕괴 → 관망/회복 대기",
                f"지금은 기존 매수/목표 레벨이 무효화된 구간. (회복 확인: {recover_level:.2f} 위로 복귀하면 다시 시나리오 재계산)",
                recover_level,
                "structure_broken",
            )
        return (
            "구조 붕괴 → 관망/회복 대기",
            "지금은 기존 매수/목표 레벨이 무효화된 구간. (회복 확인가 재계산 필요)",
            recover_level,
            "structure_broken",
        )

    if holding_type != "보유 중":
        if price_now is None:
            return "데이터 부족", "현재가(시외 포함)를 못 불러와서 상태 판정 불가", recover_level, "unknown"

        if sl0 is not None and price_now < float(sl0) * 0.998:
            return (
                "진입 실패(중단)",
                f"진입 가설이 흔들림. 우선 중단/관망. (회복 확인: {recover_level:.2f} 위 복귀 시 재평가)" if recover_level else
                "진입 가설이 흔들림. 우선 중단/관망. (회복 확인가 재평가 필요)",
                recover_level,
                "fail_soft",
            )

        if buy_low is not None and price_now <= float(buy_low) * 1.005:
            if sl0 is not None:
                return (
                    "1차 구간 진입",
                    f"분할 접근 구간. (1차: {buy_low:.2f} 근처 / 중단: {sl0:.2f} 이탈 시)",
                    recover_level,
                    "entry_1",
                )
            return (
                "1차 구간 진입",
                f"분할 접근 구간. (1차: {buy_low:.2f} 근처 / 중단 기준 재설정 필요)",
                recover_level,
                "entry_1",
            )

        if buy_high is not None and price_now <= float(buy_high) * 1.01:
            return (
                "접근 대기(근접)",
                f"아직은 대기. (1차 시작: {buy_low:.2f} ~ {buy_high:.2f} 접근 시 분할)",
                recover_level,
                "wait_near",
            )

        if tp1 is not None and price_now >= float(tp1) * 0.98:
            return (
                "상단 구간(추격 경계)",
                f"상단/저항 근접. 신규진입은 추격보다 확인 우선. (눌림 시: {buy_high:.2f} 근처 재접근)" if buy_high else
                "상단/저항 근접. 신규진입은 추격보다 확인 우선.",
                recover_level,
                "tp_zone",
            )

        if buy_high is not None and buy_low is not None:
            return (
                "대기(접근 전)",
                f"지금은 접근 전 대기. (1차 시작: {buy_low:.2f} ~ {buy_high:.2f})",
                recover_level,
                "wait_far",
            )

        return ("대기", "지금은 대기(레벨 계산값 부족).", recover_level, "wait")

    else:
        if price_now is None:
            return "데이터 부족", "현재가(시외 포함)를 못 불러와서 상태 판정 불가", recover_level, "unknown"

        if sl0 is not None and price_now < float(sl0) * 0.998:
            return (
                "방어 우선",
                f"방어 우선 구간. (0차 방어선: {sl0:.2f} 근처) 회복하면 유지, 재하락하면 비중조절",
                recover_level,
                "hold_def_soft",
            )

        if tp1 is not None and price_now >= float(tp1) * 0.98:
            return (
                "익절 구간",
                f"익절/부분정리 고려 구간. (1차 목표: {tp1:.2f} 근처) 무리한 추가매수는 비추",
                recover_level,
                "hold_tp",
            )

        if buy_low is not None and price_now >= float(buy_low) * 1.02:
            return (
                "유지(추세 유지)",
                f"유지 중심. (눌림 관심: {buy_low:.2f} ~ {buy_high:.2f}) / 이탈 시 방어: {sl0:.2f}" if (buy_high and sl0) else
                "유지 중심(레벨 일부 부족).",
                recover_level,
                "hold_trend",
            )

        if buy_low is not None and sl0 is not None:
            return (
                "애매 구간(대기/정리 고민)",
                f"애매 구간. (눌림 매수는 {buy_low:.2f} 근처부터 / 방어는 {sl0:.2f} 이탈 시)",
                recover_level,
                "hold_amb",
            )

        return ("보유", "보유 중(레벨 계산값 부족).", recover_level, "hold")


def get_volume_profile(df: pd.DataFrame, bins: int = 5):
    recent = df.tail(20)
    prices = recent["Close"]
    vols = recent["Volume"]
    if len(recent) < 5:
        return []

    min_price, max_price = prices.min(), prices.max()
    bin_edges = np.linspace(min_price, max_price, bins + 1)
    digitized = np.digitize(prices, bin_edges) - 1

    levels = []
    for i in range(bins):
        mask = digitized == i
        if not mask.any():
            continue
        total_v = vols[mask].sum()
        low = bin_edges[i]
        high = bin_edges[i + 1]
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
        price_close = float(last["Close"])
        rsi = float(last["RSI14"])

        buy_low, buy_high, tp0, tp1, tp2, sl0, sl1 = calc_levels(df, last, cfg)
        if buy_low is None or buy_high is None or tp1 is None:
            continue

        band_center = (buy_low + buy_high) / 2
        dist_band_pct = abs(price_close - band_center) / price_close * 100

        if price_close < buy_low * 0.97 or price_close > buy_high * 1.05:
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
        rr = calc_rr_ratio(price_close, tp1, sl0_new)

        results.append({
            "symbol": sym,
            "price": price_close,
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
