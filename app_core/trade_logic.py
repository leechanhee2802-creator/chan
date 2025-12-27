import numpy as np
import pandas as pd

from app_core.ui_constants import SCAN_CANDIDATES


def get_mode_config(mode_name: str):
    if mode_name == "단타":
        return {"name": "단타", "period": "3mo", "lookback_short": 10, "lookback_long": 20, "atr_mult": 1.0}
    elif mode_name == "장기":
        return {"name": "장기", "period": "1y", "lookback_short": 20, "lookback_long": 60, "atr_mult": 1.6}
    else:
        return {"name": "스윙", "period": "6mo", "lookback_short": 15, "lookback_long": 40, "atr_mult": 1.3}


def _safe_float(x, default=None):
    try:
        if x is None:
            return default
        v = float(x)
        if np.isnan(v):
            return default
        return v
    except Exception:
        return default


def calc_trend_stops(df: pd.DataFrame, cfg: dict):
    if df.empty:
        return None, None

    last = df.iloc[-1]
    price = float(last["Close"])
    ma20 = float(last["MA20"])
    atr = _safe_float(last.get("ATR14"), None)

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
    bbu = _safe_float(last.get("BBU"), None)
    rsi = _safe_float(last.get("RSI14"), 50.0)

    recent_short = df.tail(cfg["lookback_short"])
    recent_long = df.tail(cfg["lookback_long"])

    swing_high = float(recent_short["High"].max())
    box_high = float(recent_long["High"].max())

    base_res = max(swing_high * 0.995, box_high * 0.99)
    if bbu is not None:
        base_res = max(base_res, bbu * 0.98)

    tp1 = price * 1.08 if base_res <= price else base_res
    tp0 = price + (tp1 - price) * 0.6
    tp2 = tp1 + (tp1 - price) * 0.7

    if rsi is not None and rsi > 70:
        tp0 = price + (tp1 - price) * 0.5
        tp2 = tp1 + (tp1 - price) * 0.4

    return tp0, tp1, tp2


def _calc_pullback_buy_zone(price_ref: float, ma20: float, bbl: float):
    # 기존 컨셉(눌림 구간): MA20 / BBL 기반
    if price_ref > ma20:
        buy_low = ma20 * 0.98
        buy_high = ma20 * 1.01
    else:
        buy_low = bbl * 0.98
        buy_high = bbl * 1.02
    return buy_low, buy_high


def _calc_breakout_pack(df: pd.DataFrame, cfg: dict):
    """돌파(추세 재개) 트랙.
    - 최근 N일 고점(swing_high) 돌파를 트리거로 삼고
    - 돌파 시 진입/손절 기준을 ATR/퍼센트로 제시한다.
    """
    if df.empty:
        return {
            "trigger": None,
            "buy_low": None,
            "buy_high": None,
            "sl0": None,
            "tp1": None,
        }

    last = df.iloc[-1]
    atr = _safe_float(last.get("ATR14"), None)

    recent_short = df.tail(cfg["lookback_short"])
    swing_high = _safe_float(recent_short["High"].max(), None)
    if swing_high is None:
        return {"trigger": None, "buy_low": None, "buy_high": None, "sl0": None, "tp1": None}

    # 돌파 트리거(살짝 여유)
    trigger = swing_high * 1.001
    buy_low = trigger
    buy_high = trigger * 1.01

    # 돌파 손절: 트리거 아래 (ATR 기반 + 최소 퍼센트)
    pct_floor = 0.012 if cfg.get("name") == "스윙" else (0.010 if cfg.get("name") == "단타" else 0.015)
    atr_mult = 0.9 if cfg.get("name") == "단타" else (1.1 if cfg.get("name") == "스윙" else 1.4)

    sl0 = trigger * (1 - pct_floor)
    if atr is not None and atr > 0:
        sl0 = min(sl0, trigger - atr_mult * atr)
    sl0 = max(0.01, float(sl0))

    # 돌파 1차 목표: 최소 1R~1.5R 정도는 보여주도록
    r = trigger - sl0
    rr_mult = 1.2 if cfg.get("name") == "단타" else (1.5 if cfg.get("name") == "스윙" else 1.8)
    tp1 = trigger + rr_mult * r

    return {
        "trigger": float(trigger),
        "buy_low": float(buy_low),
        "buy_high": float(buy_high),
        "sl0": float(sl0),
        "tp1": float(tp1),
    }


def calc_levels_pack(df: pd.DataFrame, last: pd.Series, cfg: dict, price_ref: float | None = None):
    """레벨을 2트랙(눌림/돌파)으로 제공.
    - price_ref가 주어지면(예: 정규장 현재가) 눌림 구간 판단 분기에서 사용.
    - 목표/방어는 기본적으로 일봉 구조(df) 기반으로 산출.
    """
    if df.empty:
        return {
            "pullback": {"buy_low": None, "buy_high": None, "tp0": None, "tp1": None, "tp2": None, "sl0": None, "sl1": None},
            "breakout": {"trigger": None, "buy_low": None, "buy_high": None, "sl0": None, "tp1": None},
        }

    price_close = float(last["Close"])
    price_ref = float(price_ref) if price_ref is not None else price_close

    ma20 = float(last["MA20"])
    bbl = float(last["BBL"])

    buy_low, buy_high = _calc_pullback_buy_zone(price_ref, ma20, bbl)

    tp0, tp1, tp2 = calc_trend_targets(df, cfg)
    sl0, sl1 = calc_trend_stops(df, cfg)

    breakout = _calc_breakout_pack(df, cfg)

    return {
        "pullback": {"buy_low": buy_low, "buy_high": buy_high, "tp0": tp0, "tp1": tp1, "tp2": tp2, "sl0": sl0, "sl1": sl1},
        "breakout": breakout,
    }


# Backward compatibility (기존 app.py/scan에서 튜플을 기대할 때)
def calc_levels(df, last, cfg):
    pack = calc_levels_pack(df, last, cfg, price_ref=None)
    p = pack["pullback"]
    return p["buy_low"], p["buy_high"], p["tp0"], p["tp1"], p["tp2"], p["sl0"], p["sl1"]


def compute_state_and_action(
    holding_type: str,
    price_now: float,
    avg_price: float,
    levels: dict,
    last_row: pd.Series,
):
    """상태/행동지침.
    - levels는 pullback/breakout 정보를 함께 받을 수 있다.
    """
    buy_low = levels.get("buy_low")
    buy_high = levels.get("buy_high")
    tp1 = levels.get("tp1")
    sl0 = levels.get("sl0")
    sl1 = levels.get("sl1")

    # 돌파 트랙(있으면 사용)
    br_trigger = levels.get("breakout_trigger")
    br_buy_low = levels.get("breakout_buy_low")
    br_buy_high = levels.get("breakout_buy_high")
    br_sl0 = levels.get("breakout_sl0")
    br_tp1 = levels.get("breakout_tp1")

    ma20 = _safe_float(last_row.get("MA20", np.nan), None)

    recover_candidates = []
    if buy_high is not None:
        recover_candidates.append(float(buy_high) * 1.005)
    if ma20 is not None:
        recover_candidates.append(float(ma20) * 1.01)
    recover_level = max(recover_candidates) if recover_candidates else None

    # 구조 붕괴: 기존은 0.998 고정이라 과민할 수 있음 → 완충
    structure_broken = False
    if price_now is not None and sl1 is not None:
        # ATR 기반 완충(없으면 0.35%)
        atr = _safe_float(last_row.get("ATR14", None), None)
        if atr is not None and price_now > 0:
            buf = max(0.0035, 0.15 * (atr / price_now))
        else:
            buf = 0.0035
        if price_now < float(sl1) * (1 - buf):
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
            return "데이터 부족", "현재가를 못 불러와서 상태 판정 불가", recover_level, "unknown"

        # ✅ 신규진입에서 '너무 위'에 떠있는 경우: 눌림만 기다리게 하지 말고 돌파 트랙 제시
        if buy_high is not None and price_now > float(buy_high) * 1.06 and br_trigger is not None:
            if price_now < float(br_trigger) * 0.997:
                return (
                    "돌파 대기(추세 재개 확인)",
                    f"현재가는 눌림구간(아래)에서 멀어요. '돌파 확인' 트랙 권장: {br_trigger:.2f} 상향 돌파/안착 시 진입 검토.",
                    recover_level,
                    "breakout_wait",
                )
            if br_buy_high is not None and price_now <= float(br_buy_high) * 1.002:
                sl_txt = f" / 중단: {br_sl0:.2f}" if br_sl0 is not None else ""
                return (
                    "돌파 구간 진입",
                    f"추세 재개(돌파) 구간. (진입: {br_buy_low:.2f}~{br_buy_high:.2f}{sl_txt})",
                    recover_level,
                    "breakout_entry",
                )
            return (
                "돌파 후 추격 경계",
                f"돌파는 나왔지만 가격이 너무 위예요. 무리한 추격 대신, {br_trigger:.2f} 부근 재확인/눌림 대기 권장.",
                recover_level,
                "breakout_chase",
            )

        if sl0 is not None and price_now < float(sl0) * 0.998:
            return (
                "진입 실패(중단)",
                f"진입 가설이 흔들림. 우선 중단/관망. (회복 확인: {recover_level:.2f} 위 복귀 시 재평가)" if recover_level else
                "진입 가설이 흔들림. 우선 중단/관망. (회복 확인가 재계산 필요)",
                recover_level,
                "fail_soft",
            )

        if buy_low is not None and price_now <= float(buy_low) * 1.005:
            if sl0 is not None:
                return (
                    "1차 구간 진입(눌림)",
                    f"분할 접근 구간. (눌림 1차: {buy_low:.2f} 근처 / 중단: {sl0:.2f} 이탈 시)",
                    recover_level,
                    "entry_1",
                )
            return (
                "1차 구간 진입(눌림)",
                f"분할 접근 구간. (눌림 1차: {buy_low:.2f} 근처 / 중단 기준 재설정 필요)",
                recover_level,
                "entry_1",
            )

        if buy_high is not None and price_now <= float(buy_high) * 1.01:
            return (
                "접근 대기(근접)",
                f"아직은 대기. (눌림 1차: {buy_low:.2f} ~ {buy_high:.2f} 접근 시 분할)",
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
                f"지금은 접근 전 대기. (눌림 1차: {buy_low:.2f} ~ {buy_high:.2f})",
                recover_level,
                "wait_far",
            )

        return ("대기", "지금은 대기(레벨 계산값 부족).", recover_level, "wait")

    else:
        if price_now is None:
            return "데이터 부족", "현재가를 못 불러와서 상태 판정 불가", recover_level, "unknown"

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

        # 스캔은 '눌림' 후보 찾기라 기존 pullback 튜플 사용
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
