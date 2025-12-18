import numpy as np

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
            score += 2; details.append(f"나스닥 선물 +{nas_chg:.2f}% (강한 상승)")
        elif nas_chg >= 0.3:
            score += 1; details.append(f"나스닥 선물 +{nas_chg:.2f}% (완만한 상승)")
        elif nas_chg <= -1.0:
            score -= 2; details.append(f"나스닥 선물 {nas_chg:.2f}% (강한 하락)")
        elif nas_chg <= -0.3:
            score -= 1; details.append(f"나스닥 선물 {nas_chg:.2f}% (완만한 하락)")

    us10y = rf.get("us10y")
    if us10y is not None:
        if us10y < 4.0:
            score += 2; details.append(f"미 10년물 {us10y:.2f}% (금리 우호)")
        elif us10y < 4.2:
            score += 1; details.append(f"미 10년물 {us10y:.2f}% (무난)")
        elif us10y > 4.4:
            score -= 2; details.append(f"미 10년물 {us10y:.2f}% (금리 부담)")
        else:
            score -= 1; details.append(f"미 10년물 {us10y:.2f}% (다소 부담)")

    dxy = rf.get("dxy")
    if dxy is not None:
        if dxy < 104:
            score += 1; details.append(f"DXY {dxy:.2f} (달러 약세 → Risk-on 우호)")
        elif dxy > 106:
            score -= 1; details.append(f"DXY {dxy:.2f} (달러 강세 → Risk-off 경계)")

    for e in etfs:
        sym = e.get("symbol")
        chg = e.get("chg_pct")
        if chg is None:
            continue
        if chg >= 0.5:
            score += 1; details.append(f"{sym} +{chg:.2f}% (ETF 강세)")
        elif chg <= -0.5:
            score -= 1; details.append(f"{sym} {chg:.2f}% (ETF 약세)")

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

    return score, label, " · ".join(details)

def _clamp(x, lo=0.0, hi=100.0):
    try:
        x = float(x)
    except Exception:
        return lo
    return max(lo, min(hi, x))

def score_to_text(score_0_100: float) -> str:
    s = float(score_0_100)
    if s >= 70:
        return "위험선호 우세"
    elif s >= 65:
        return "양호"
    elif s >= 52:
        return "반등 시도"
    elif s >= 45:
        return "추세 불안"
    else:
        return "위험회피 우세"

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

def compute_market_verdict_scores(overview: dict, bigtech_list_len: int = 1):
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
    n = max(1, int(bigtech_list_len or 1))
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
