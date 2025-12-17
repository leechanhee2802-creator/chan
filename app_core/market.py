"""Market data helpers and snapshot utilities."""

import time
from typing import Tuple

import numpy as np
import requests
import streamlit as st
import yfinance as yf

from app_core.symbols import BIGTECH_LIST, SECTOR_ETF_LIST


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
    """
    프리/정규/애프터 포함 가장 최근 1분봉 Close를 사용(있으면).
    - "상태 전환" 판정에 사용
    """
    try:
        t = yf.Ticker(symbol)
        df = t.history(period="1d", interval="1m", auto_adjust=False, prepost=True)
        if df.empty:
            return None
        return float(df["Close"].iloc[-1])
    except Exception:
        return None


def safe_last_change_info(ticker_str: str):
    """
    (기존 유지) 주로 개별 종목/ETF/지수 등에 사용.
    세계지표(선물/10년물/DXY)는 아래의 스냅샷 함수를 따로 사용해 튐/기준혼선 해결.
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


def compute_change_percent(last, prev_close):
    if last is None or prev_close is None:
        return np.nan
    if isinstance(last, float) and np.isnan(last):
        return np.nan
    if isinstance(prev_close, float) and np.isnan(prev_close):
        return np.nan
    if prev_close == 0:
        return np.nan
    return (float(last) / float(prev_close) - 1.0) * 100.0


def compute_tnx(last_tnx, prev_close_tnx):
    """
    ^TNX는 '수익률 * 10' 값.
    - 표시 수익률(%): last_tnx / 10
    - 변화(bp): (last_tnx - prev_close_tnx) * 10
      (ΔTNX/10 %p * 100 = ΔTNX * 10 bp)
    """
    if last_tnx is None or prev_close_tnx is None:
        return np.nan, np.nan
    if (isinstance(last_tnx, float) and np.isnan(last_tnx)) or (isinstance(prev_close_tnx, float) and np.isnan(prev_close_tnx)):
        return np.nan, np.nan
    yield_pct, delta_bp = float(last_tnx) / 10.0, (float(last_tnx) - float(prev_close_tnx)) * 10.0
    return yield_pct, delta_bp


@st.cache_data(ttl=30, show_spinner=False)
def fetch_yf_snapshot(symbols, _refresh_key: int):
    """
    _refresh_key가 바뀌면 캐시 무효화.
    ttl 30초로 너무 자주 튀는 느낌 완화.
    """
    out = {}
    for sym in symbols:
        try:
            t = yf.Ticker(sym)

            last = None
            prev_close = None

            try:
                info = t.fast_info
            except Exception:
                info = None

            if info:
                last = info.get("lastPrice", None) or info.get("last_price", None)
                prev_close = info.get("previousClose", None) or info.get("previous_close", None)

            if last is None or prev_close is None:
                hist = t.history(period="5d", interval="1d")
                if not hist.empty:
                    last = float(hist["Close"].iloc[-1])
                    if len(hist) >= 2:
                        prev_close = float(hist["Close"].iloc[-2])
                    else:
                        prev_close = float(hist["Close"].iloc[-1])

            out[sym] = {
                "last": float(last) if last is not None else np.nan,
                "prev_close": float(prev_close) if prev_close is not None else np.nan,
                "ts": time.time(),
            }
        except Exception:
            out[sym] = {"last": np.nan, "prev_close": np.nan, "ts": time.time()}
    return out


@st.cache_data(ttl=60)
def get_us_market_overview():
    """
    ✅ 세계지표: NQ=F, ES=F, ^TNX, DXY는 스냅샷 기반으로 통일(전일종가 기준 + 10년물 bp)
    ✅ 나머지(지수/ETF/빅테크/섹터)는 기존 방식 유지
    """
    overview = {}

    if "refresh_key" not in st.session_state:
        st.session_state["refresh_key"] = 0

    snap_symbols = ["NQ=F", "ES=F", "^TNX", "DX-Y.NYB"]
    snap = fetch_yf_snapshot(snap_symbols, st.session_state["refresh_key"])

    nq_last, nq_prev = snap["NQ=F"]["last"], snap["NQ=F"]["prev_close"]
    es_last, es_prev = snap["ES=F"]["last"], snap["ES=F"]["prev_close"]

    nq_chg = compute_change_percent(nq_last, nq_prev)
    es_chg = compute_change_percent(es_last, es_prev)

    overview["futures"] = {
        "nasdaq": {"last": float(nq_last) if not (isinstance(nq_last, float) and np.isnan(nq_last)) else None,
                   "chg_pct": float(nq_chg) if not (isinstance(nq_chg, float) and np.isnan(nq_chg)) else None,
                   "state": "SNAP"},
        "sp500":  {"last": float(es_last) if not (isinstance(es_last, float) and np.isnan(es_last)) else None,
                   "chg_pct": float(es_chg) if not (isinstance(es_chg, float) and np.isnan(es_chg)) else None,
                   "state": "SNAP"},
    }

    tnx_last, tnx_prev = snap["^TNX"]["last"], snap["^TNX"]["prev_close"]
    us10y_yield, us10y_bp = compute_tnx(tnx_last, tnx_prev)

    dxy_last, dxy_prev = snap["DX-Y.NYB"]["last"], snap["DX-Y.NYB"]["prev_close"]
    dxy_chg = compute_change_percent(dxy_last, dxy_prev)

    overview["rates_fx"] = {
        "us10y": float(us10y_yield) if not (isinstance(us10y_yield, float) and np.isnan(us10y_yield)) else None,
        "us10y_bp": float(us10y_bp) if not (isinstance(us10y_bp, float) and np.isnan(us10y_bp)) else None,
        "us10y_state": "SNAP",
        "dxy": float(dxy_last) if not (isinstance(dxy_last, float) and np.isnan(dxy_last)) else None,
        "dxy_chg": float(dxy_chg) if not (isinstance(dxy_chg, float) and np.isnan(dxy_chg)) else None,
        "dxy_state": "SNAP",
    }

    overview["fgi"] = fetch_fgi()

    idx = {}
    for name, ticker in [("nasdaq", "^IXIC"), ("sp500", "^GSPC")]:
        last, chg_pct, _state = safe_last_change_info(ticker)
        idx[name] = {"last": last, "chg_pct": chg_pct, "state": _state}
    overview["indexes"] = idx

    etfs = [
        get_etf_price_with_prepost("QQQ", "QQQ"),
        get_etf_price_with_prepost("VOO", "VOO"),
        get_etf_price_with_prepost("SOXX", "SOXX"),
    ]
    overview["etfs"] = etfs

    bt_layer = []
    bt_score = 0
    for sym, name in BIGTECH_LIST:
        last, chg, mkt_state = safe_last_change_info(sym)
        layer = {"symbol": sym, "chg_pct": chg, "market_state": mkt_state}
        if last is not None:
            layer["last"] = last
        if chg is not None:
            layer["chg_pct"] = chg
            if chg >= 0.5:
                bt_score += 1
            elif chg >= 0:
                bt_score += 0.5
            elif chg <= -1:
                bt_score -= 1
        bt_layer.append(layer)

    overview["bigtech"] = {"items": bt_layer, "score": bt_score}

    sector_layer = []
    sec_score = 0
    for name, sym in SECTOR_ETF_LIST:
        last, chg, mkt_state = safe_last_change_info(sym)
        layer = {"name": name, "symbol": sym, "chg_pct": chg, "market_state": mkt_state}
        if last is not None:
            layer["last"] = last
        if chg is not None:
            if chg >= 0.5:
                sec_score += 0.8
            elif chg >= 0:
                sec_score += 0.5
            elif chg <= -1:
                sec_score -= 0.8
        sector_layer.append(layer)

    overview["sector"] = {"items": sector_layer, "score": sec_score}
    return overview


def compute_market_score(overview: dict):
    if not overview:
        return 0, "데이터 없음", ""

    futures = overview.get("futures", {}) or {}
    rf = overview.get("rates_fx", {}) or {}
    etfs = overview.get("etfs", []) or []
    bigtech = overview.get("bigtech", {}) or {}

    score = 0
    detail_lines = []

    for k in ["nasdaq", "sp500"]:
        fv = futures.get(k, {}) or {}
        chg = fv.get("chg_pct")
        if chg is not None:
            if chg >= 0.7:
                score += 2
                detail_lines.append(f"선물({k}) +2")
            elif chg >= 0.2:
                score += 1
                detail_lines.append(f"선물({k}) +1")
            elif chg <= -1.0:
                score -= 2
                detail_lines.append(f"선물({k}) -2")
            elif chg <= -0.5:
                score -= 1
                detail_lines.append(f"선물({k}) -1")

    us10y = rf.get("us10y_bp")
    if us10y is not None:
        if us10y > 4:
            score -= 1
            detail_lines.append("10년물 금리 상승(-)")
        elif us10y < -4:
            score += 1
            detail_lines.append("10년물 금리 하락(+)")

    dxy = rf.get("dxy_chg")
    if dxy is not None:
        if dxy > 0.2:
            score -= 1
            detail_lines.append("달러 강세(-)")
        elif dxy < -0.2:
            score += 1
            detail_lines.append("달러 약세(+)")

    etf_chgs = [e.get("chg_pct") for e in etfs if e.get("chg_pct") is not None]
    if etf_chgs:
        avg_etf = float(np.mean(etf_chgs))
        if avg_etf >= 1.0:
            score += 2
            detail_lines.append("ETF 선행 강세(+2)")
        elif avg_etf >= 0.3:
            score += 1
            detail_lines.append("ETF 선행 강세(+1)")
        elif avg_etf <= -1.0:
            score -= 2
            detail_lines.append("ETF 선행 약세(-2)")
        elif avg_etf <= -0.3:
            score -= 1
            detail_lines.append("ETF 선행 약세(-1)")

    bt_score = bigtech.get("score", 0)
    if bt_score >= 3:
        score += 2
        detail_lines.append("빅테크 강세(+2)")
    elif bt_score >= 1:
        score += 1
        detail_lines.append("빅테크 강보합(+1)")
    elif bt_score <= -3:
        score -= 2
        detail_lines.append("빅테크 약세(-2)")

    label = "우호" if score >= 3 else "중립" if score >= -1 else "경계"
    detail = " / ".join(detail_lines)
    return score, label, detail


def _clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))


def score_to_text(score_0_100: float) -> str:
    if score_0_100 >= 65:
        return "긍정적"
    if score_0_100 >= 55:
        return "점진 개선"
    if score_0_100 >= 45:
        return "중립"
    if score_0_100 >= 35:
        return "신중 필요"
    return "주의"


def market_state_badge_from_etfs(etfs: list):
    stt = ""
    if etfs:
        for e in etfs:
            ms = (e.get("market_state") or "").strip()
            if ms:
                stt = ms
                break
    if stt == "PRE":
        return "🟡 프리장", "chip chip-blue"
    if stt == "POST":
        return "🟣 애프터장", "chip chip-blue"
    if stt == "REGULAR":
        return "🟢 정규장", "chip chip-green"
    if stt:
        return f"⚪ 장 상태: {stt}", "chip chip-blue"
    return "⚪ 장 상태: 확인중", "chip chip-blue"


def compute_market_verdict_scores(overview: dict):
    if not overview:
        return None

    mkt_score, _, _ = compute_market_score(overview)
    macro_0_100 = _clamp((mkt_score + 8) / 16 * 100)

    etfs = overview.get("etfs", []) or []
    etf_chgs = [e.get("chg_pct") for e in etfs if e.get("chg_pct") is not None]
    if etf_chgs:
        avg_etf = float(np.mean(etf_chgs))
        etf_0_100 = _clamp(50 + avg_etf * 20)
    else:
        etf_0_100 = 50.0

    idx = overview.get("indexes", {}) or {}
    ixic = idx.get("nasdaq", {}) or {}
    gspc = idx.get("sp500", {}) or {}
    idx_chgs = [v for v in [ixic.get("chg_pct"), gspc.get("chg_pct")] if v is not None]
    if idx_chgs:
        avg_idx = float(np.mean(idx_chgs))
        index_0_100 = _clamp(50 + avg_idx * 20)
    else:
        fut = overview.get("futures", {}) or {}
        nas_f = (fut.get("nasdaq", {}) or {}).get("chg_pct")
        if nas_f is not None:
            index_0_100 = _clamp(50 + float(nas_f) * 18)
        else:
            index_0_100 = 50.0

    bt = overview.get("bigtech", {}) or {}
    bt_score = bt.get("score", 0)
    n = max(1, len(BIGTECH_LIST))
    leader_0_100 = _clamp(50 + (float(bt_score) / n) * 30)

    line_macro = f"세계지표: {score_to_text(macro_0_100)}"

    etf_text = score_to_text(etf_0_100)
    if etf_0_100 >= 65:
        etf_text = f"{etf_text} (정규장 확인 필요)"
    elif etf_0_100 < 50:
        etf_text = f"{etf_text} (리스크 경계)"
    else:
        etf_text = f"{etf_text} (대기)"
    line_etf = f"ETF 선행: {etf_text}"

    idx_text = score_to_text(index_0_100)
    if 52 <= index_0_100 < 60:
        idx_text = "반등 시도 중이나 추세 불안"
    elif 45 <= index_0_100 < 52:
        idx_text = "추세 불안"
    line_index = f"지수 점수: {idx_text}"

    leader_text = score_to_text(leader_0_100)
    if 58 <= leader_0_100 < 68:
        leader_text = "상단 부담"
    elif 52 <= leader_0_100 < 58:
        leader_text = "힘 부족"
    elif leader_0_100 < 52:
        leader_text = "주도력 상실"
    elif leader_0_100 >= 68:
        leader_text = "주도력 확실"
    line_leader = f"빅테크: {leader_text}"

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
