import numpy as np
import pandas as pd

from ui_constants import SCAN_CANDIDATES

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

def compute_state_and_action(holding_type: str, price_now: float, avg_price: float, levels: dict, last_row: pd.Series):
    buy_low = levels.get("buy_low")
    buy_high = levels.get("buy_high")
    tp1 = levels.get("tp1")
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

def scan_new_entry_candidates(cfg: dict, max_results: int, get_us_market_overview_fn, compute_market_score_fn, analysis_mod, market_mod):
    results = []
    ov = get_us_market_overview_fn()
    market_score, _, _ = compute_market_score_fn(ov)

    for sym in SCAN_CANDIDATES:
        df = market_mod.get_price_data(sym, cfg["period"])
        if df is None or df.empty:
            continue
        df = analysis_mod.add_indicators(df)
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

        bias = analysis_mod.short_term_bias(last)
        score = 0
        if "상방" in bias:
            score += 2
        elif "중립" in bias:
            score += 1

        score += max(0, 3 - dist_band_pct)
        score += max(0, 2 - abs(rsi - 50) / 10)

        sl0_new = buy_low * 0.97
        rr = analysis_mod.calc_rr_ratio(price_close, tp1, sl0_new)

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
