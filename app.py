import numpy as np
import streamlit as st
from app_core import analysis

from app_core.ai import _ai_make_cache_key, ai_summarize_and_explain, request_ai_generation
from app_core.analysis import (
    add_indicators,
    build_risk_alerts,
    calc_gap_info,
    calc_levels,
    calc_rr_ratio,
    get_heavy_days,
    get_intraday_5m,
    get_intraday_5m_score,
    get_mode_config,
    get_price_data,
    scan_new_entry_candidates,
    short_term_bias,
)
from app_core.config import configure_page, inject_global_styles
from app_core.market import (
    compute_market_score,
    compute_market_verdict_scores,
    get_last_extended_price,
    get_us_market_overview,
    get_usdkrw_rate,
    market_state_badge_from_etfs,
)
from app_core.state import initialize_session_state
from app_core.symbols import POPULAR_SYMBOLS, normalize_symbol


configure_page()
inject_global_styles()
initialize_session_state()
# =====================================
# 레이아웃: 메인 + 사이드
# =====================================
col_main, col_side = st.columns([3, 1])

# ---- 오른쪽: 즐겨찾기 / 최근검색 ----
with col_side:
    st.subheader("⭐ 즐겨찾기 & 최근 종목")

    tab_fav, tab_recent = st.tabs(["⭐ 즐겨찾기", "🕒 최근 검색"])
    clicked_symbol = None

    with tab_fav:
        favs = st.session_state["favorite_symbols"]
        if not favs:
            st.caption("아직 즐겨찾기한 종목이 없습니다.")
        else:
            for sym in favs:
                if st.button(sym, key=f"fav_{sym}"):
                    clicked_symbol = sym

    with tab_recent:
        recents = list(reversed(st.session_state["recent_symbols"]))
        if not recents:
            st.caption("최근 조회 종목이 없습니다.")
        else:
            for sym in recents:
                if st.button(sym, key=f"recent_{sym}"):
                    clicked_symbol = sym

    if clicked_symbol:
        st.session_state["selected_symbol"] = clicked_symbol
        st.session_state["symbol_input"] = clicked_symbol
        st.session_state["run_from_side"] = True

# ---- 왼쪽: 메인 ----
with col_main:
    st.title("📈 내 주식 자동판독기")
    st.caption("시장 개요 + 개별 종목 판독 + 레이어/갭/ATR/장중 흐름을 한 화면에서 확인")

    # 1) 미국 시장 개요 + 레이어
    with st.expander("🌍 미국 시장 실시간 흐름 (보조지표 + 레이어)", expanded=True):
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            refresh = st.button("🔄 새로고침", key="refresh_overview")
        if refresh:
            # ✅ 패치: refresh_key 올리고 캐시 clear로 스냅샷/세계지표 튐 완화
            st.session_state["refresh_key"] += 1
            st.cache_data.clear()

        with st.spinner("미국 선물 · 금리 · 달러 · ETF · 레이어 상황 불러오는 중..."):
            ov = get_us_market_overview()

        score_mkt, label_mkt, detail_mkt = market.compute_market_score(ov)

        fut = ov.get("futures", {})
        rf = ov.get("rates_fx", {})
        etfs = ov.get("etfs", [])
        bigtech_layer = ov.get("bigtech", {})
        sector_layer = ov.get("sector", {})

        nas = fut.get("nasdaq", {})
        es = fut.get("sp500", {})

        col1, col2, col3 = st.columns(3)
        with col1:
            lastv = nas.get("last")
            chg = nas.get("chg_pct")
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">나스닥 선물 (전일 종가 기준)</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{lastv:.1f}</div>' if lastv is not None else '<div class="metric-value">N/A</div>', unsafe_allow_html=True)
            if chg is not None:
                st.markdown(f'<div class="metric-delta-pos">↑ {chg:.2f}%</div>' if chg >= 0 else f'<div class="metric-delta-neg">↓ {abs(chg):.2f}%</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            lastv = es.get("last")
            chg = es.get("chg_pct")
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">S&P500 선물 (전일 종가 기준)</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{lastv:.1f}</div>' if lastv is not None else '<div class="metric-value">N/A</div>', unsafe_allow_html=True)
            if chg is not None:
                st.markdown(f'<div class="metric-delta-pos">↑ {chg:.2f}%</div>' if chg >= 0 else f'<div class="metric-delta-neg">↓ {abs(chg):.2f}%</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">시장 점수</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{score_mkt} / 8</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="small-muted">{label_mkt}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.caption("※ 범위: -8 ~ 8 | 선물·금리·달러·ETF 기준 종합")

        verdict = market.compute_market_verdict_scores(ov)
        session_badge, session_cls = market.market_state_badge_from_etfs(etfs)

        if verdict:
            st.markdown(
                f"""
                <div class="card-soft">
                  <div class="layer-title-en">MARKET VERDICT</div>
                  <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin-bottom:8px;">
                    <span class="{session_cls}">{session_badge}</span>
                    <span class="chip chip-blue">Macro {verdict['macro']:.0f}</span>
                    <span class="chip chip-blue">ETF {verdict['etf']:.0f}</span>
                    <span class="chip chip-blue">Index {verdict['index']:.0f}</span>
                    <span class="chip chip-blue">BigTech {verdict['leader']:.0f}</span>
                  </div>

                  <div style="line-height:1.55;">
                    <div>🔍 현재 시장 판독</div>
                    <div class="small-muted" style="margin-top:6px;">
                      • {verdict['lines'][0]}<br/>
                      • {verdict['lines'][1]}<br/>
                      • {verdict['lines'][2]}<br/>
                      • {verdict['lines'][3]}
                    </div>
                  </div>

                  <div style="margin-top:10px;">
                    <div style="font-weight:700;">📌 결론</div>
                    <div style="margin-top:4px;">
                      → {verdict['conclusion']}<br/>
                      → {verdict['holder_line']}
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if detail_mkt:
            st.caption("· " + detail_mkt)

        st.markdown("---")

        col4, col5, col6 = st.columns(3)
        with col4:
            us10y = rf.get("us10y")
            us10y_bp = rf.get("us10y_bp")

            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">미 10년물 (TNX/10) · 변화(bp)</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{us10y:.2f}%</div>' if us10y is not None else '<div class="metric-value">N/A</div>', unsafe_allow_html=True)

            # ✅ 금리 변화는 bp로 표시: 금리↑(bp+)는 빨강, 금리↓(bp-)는 초록
            if us10y_bp is not None:
                if us10y_bp > 0:
                    st.markdown(f'<div class="metric-delta-neg">▲ {us10y_bp:.1f}bp (금리↑)</div>', unsafe_allow_html=True)
                elif us10y_bp < 0:
                    st.markdown(f'<div class="metric-delta-pos">▼ {abs(us10y_bp):.1f}bp (금리↓)</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="metric-delta-pos">0.0bp</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        with col5:
            dxy = rf.get("dxy")
            dxy_chg = rf.get("dxy_chg")
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">달러 인덱스 (DXY)</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{dxy:.2f}</div>' if dxy is not None else '<div class="metric-value">N/A</div>', unsafe_allow_html=True)
            if dxy_chg is not None:
                st.markdown(f'<div class="metric-delta-pos">↑ {dxy_chg:.2f}%</div>' if dxy_chg >= 0 else f'<div class="metric-delta-neg">↓ {abs(dxy_chg):.2f}%</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col6:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">참고</div>', unsafe_allow_html=True)
            st.markdown('<div class="small-muted">※ 선물/10년물/DXY는 "스냅샷(prev close 기준)"으로 통일해 튐을 완화했습니다.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        st.caption("📈 ETF 3대장 (QQQ · VOO · SOXX)")
        if etfs:
            cols_etf = st.columns(3)
            for i, e in enumerate(etfs):
                with cols_etf[i]:
                    sym = e.get("symbol")
                    current = e.get("current")
                    chg = e.get("chg_pct")
                    basis = e.get("basis")
                    state = e.get("market_state", "")

                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-label">{sym}</div>', unsafe_allow_html=True)
                    value_str = f"{current:.2f}" if current is not None else "N/A"
                    st.markdown(f'<div class="metric-value">{value_str}</div>', unsafe_allow_html=True)
                    if chg is not None:
                        st.markdown(f'<div class="metric-delta-pos">↑ {chg:.2f}%</div>' if chg >= 0 else f'<div class="metric-delta-neg">↓ {abs(chg):.2f}%</div>', unsafe_allow_html=True)
                    extra = basis + (f" · 상태: {state}" if state else "")
                    st.markdown(f'<div class="small-muted">{extra}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            st.caption("※ %는 전일 종가 대비 기준입니다.")
        else:
            st.write("ETF 데이터를 불러오지 못했습니다.")

        st.markdown("---")

        # BIG TECH LAYER
        bt_score = bigtech_layer.get("score", 0)
        bt_items = bigtech_layer.get("items", [])
        st.markdown('<div class="card-soft">', unsafe_allow_html=True)
        st.markdown('<div class="layer-title-en">BIG TECH LAYER</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chip chip-green">빅테크 강도 점수: {bt_score}</div>', unsafe_allow_html=True)
        for it in bt_items:
            sym = it.get("symbol")
            chg = it.get("chg")
            if sym is None:
                continue
            if chg is None:
                continue
            sign = "+" if chg > 0 else ""
            cls = "layer-chg-pos" if chg > 0 else ("layer-chg-neg" if chg < 0 else "layer-chg-flat")
            st.markdown(
                f'<div class="layer-row"><span class="layer-symbol">{sym}</span>'
                f'<span class="{cls}">{sign}{chg:.2f}%</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

        # SECTOR ROTATION LAYER
        sec_score = sector_layer.get("score", 0)
        sec_items = sector_layer.get("items", [])
        st.markdown('<div class="card-soft">', unsafe_allow_html=True)
        st.markdown('<div class="layer-title-en">SECTOR ROTATION LAYER</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chip chip-blue">섹터 점수: {sec_score}</div>', unsafe_allow_html=True)
        for it in sec_items:
            label = it.get("label")
            chg = it.get("chg")
            if label is None:
                continue
            if chg is None:
                continue
            sign = "+" if chg > 0 else ""
            cls = "layer-chg-pos" if chg > 0 else ("layer-chg-neg" if chg < 0 else "layer-chg-flat")
            st.markdown(
                f'<div class="layer-row"><span class="layer-symbol">{label}</span>'
                f'<span class="{cls}">{sign}{chg:.2f}%</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown('<div class="small-muted">※ 섹터별 강도 흐름을 통해 쏠림을 한 눈에 체크.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # 2) 내 종목 자동 판독기
    st.subheader("🔍 내 종목 자동 판독기 + 실전 보조지표")

    col_top1, col_top2 = st.columns(2)
    with col_top1:
        user_symbol = st.text_input(
            "종목 이름/티커 (예: NVDA, 엔비디아, META, TQQQ)",
            key="symbol_input",
        )
        holding_type = st.radio("보유 상태", ["보유 중", "신규 진입 검토"], horizontal=True)

    with col_top2:
        mode_name = st.selectbox("투자 모드 선택", ["단타", "스윙", "장기"], index=1)
        commission_pct = st.number_input(
            "왕복 수수료/비용(%) (기본 0.2% 가정)",
            min_value=0.0, max_value=2.0,
            value=0.2, step=0.05,
        )

    cfg = analysis.get_mode_config(mode_name)

    prefix = (user_symbol or "").strip().upper().replace(" ", "")
    candidates = sorted(set(symbols.POPULAR_SYMBOLS + st.session_state["recent_symbols"]))
    suggestions = [s for s in candidates if s.startswith(prefix)] if prefix else []
    if suggestions:
        st.caption("자동완성 도움: " + ", ".join(suggestions[:6]))

    # 보유 정보
    col_mid1, col_mid2 = st.columns(2)
    avg_price = 0.0
    shares = 0
    if holding_type == "보유 중":
        with col_mid1:
            avg_price = st.number_input("내 평단가 (USD)", min_value=0.0, value=0.0, step=0.01)
        with col_mid2:
            shares = st.number_input("보유 수량 (주)", min_value=0, value=0, step=1)

    run_click = st.button("🚀 분석하기", key="run_analyze")
    run_from_side = st.session_state.get("run_from_side", False)
    run = run_click or run_from_side
    st.session_state["run_from_side"] = False

    # ✅ run 시점에 결과 유지 파라미터를 저장 (AI rerun에도 결과 유지)
    if run:
        st.session_state["show_result"] = True
        st.session_state["analysis_params"] = {
            "user_symbol": user_symbol,
            "holding_type": holding_type,
            "mode_name": mode_name,
            "commission_pct": commission_pct,
            "avg_price": float(avg_price or 0.0),
            "shares": int(shares or 0),
        }
        st.session_state["scroll_to_result"] = True

    # ✅ show_result가 True면, run이 False여도 결과를 계속 렌더
    if st.session_state.get("show_result") and st.session_state.get("analysis_params"):
        _p = st.session_state.get("analysis_params") or {}
        user_symbol = _p.get("user_symbol", user_symbol)
        holding_type = _p.get("holding_type", holding_type)
        mode_name = _p.get("mode_name", mode_name)
        commission_pct = _p.get("commission_pct", commission_pct)
        avg_price = float(_p.get("avg_price", avg_price or 0.0) or 0.0)
        shares = int(_p.get("shares", shares or 0) or 0)
        cfg = analysis.get_mode_config(mode_name)

    # 스캐너
    with st.expander("🛰 신규 진입 스캐너 (간단 버전)", expanded=False):
        col_s1, col_s2 = st.columns([1, 1])
        with col_s1:
            scan_click = st.button("📊 스캐너 실행", key="run_scan")
        with col_s2:
            close_scan = st.button("🧹 결과 닫기", key="close_scan")

        if close_scan:
            st.session_state["scan_results"] = None
            st.success("스캐너 결과를 닫았습니다.")
            st.rerun()

        if scan_click:
            with st.spinner("신규 진입 후보 종목 스캔 중..."):
                scan_mkt_score, scan_list = analysis.scan_new_entry_candidates(cfg)
            st.session_state["scan_results"] = {"market_score": scan_mkt_score, "items": scan_list}

        scan_data = st.session_state.get("scan_results")
        if scan_data:
            scan_mkt_score = scan_data["market_score"]
            scan_list = scan_data["items"]

            if scan_mkt_score <= -4:
                st.warning("시장 점수가 강한 Risk-off 구간입니다. 신규 진입은 특히 보수적으로.")

            if not scan_list:
                st.write("조건을 만족하는 신규 진입 후보 종목이 없습니다.")
            else:
                st.caption(f"총 **{len(scan_list)}개** 종목이 조건을 만족했습니다.")
                scan_clicked_symbol = None

                for item in scan_list:
                    sym = item["symbol"]
                    price = item["price"]
                    bias = item["bias"]
                    score_val = item["score"]
                    rr = item.get("rr")

                    rr_txt = f"{rr:.2f}:1" if rr is not None else "N/A"
                    st.markdown(
                        f"**{sym}** | 현재가(일봉 종가) **{price:.2f}** | 단기흐름: {bias} | 스코어 **{score_val:.1f}** | 손익비 {rr_txt}"
                    )
                    go = st.button(f"🔍 {sym} 바로 분석", key=f"scan_go_{sym}")
                    if go:
                        scan_clicked_symbol = sym

                if scan_clicked_symbol is not None:
                    st.session_state["pending_symbol"] = scan_clicked_symbol
                    st.session_state["scroll_to_result"] = True
                    st.rerun()

    if not st.session_state.get("show_result"):
        st.stop()

    # ---- 결과 렌더 ----
    symbol = symbols.normalize_symbol(user_symbol)
    display_name = user_symbol.strip() if user_symbol else ""

    if not symbol:
        st.error("❌ 종목 이름 또는 티커가 비어있습니다. 다시 입력해 주세요.")
        st.stop()

    with st.spinner("데이터 불러오는 중..."):
        ov = market.get_us_market_overview()
        fgi = ov.get("fgi")

        df = analysis.get_price_data(symbol, cfg["period"])
        if df.empty:
            st.error("❌ 이 종목은 선택한 기간 동안 데이터가 부족하거나, 티커가 잘못되었습니다.")
            st.stop()

        df = analysis.add_indicators(df)
        if df.empty:
            st.error("❌ 지표 계산에 필요한 데이터가 부족합니다.")
            st.stop()

        last = df.iloc[-1]
        df_5m = analysis.get_intraday_5m(symbol)

    # 최근/즐겨찾기
    if symbol not in st.session_state["recent_symbols"]:
        st.session_state["recent_symbols"].append(symbol)
        st.session_state["recent_symbols"] = st.session_state["recent_symbols"][-30:]

    # 가격: 레벨은 일봉, 상태는 시외 포함 최근가
    price_close = float(last["Close"])
    ext_price = market.get_last_extended_price(symbol)
    price_now = float(ext_price) if ext_price is not None else price_close

    profit_pct = (price_now - avg_price) / avg_price * 100 if avg_price > 0 else 0.0
    total_pnl = (price_now - avg_price) * shares if (shares > 0 and avg_price > 0) else 0.0

    buy_low, buy_high, tp0, tp1, tp2, sl0, sl1 = analysis.calc_levels(df, last, cfg)

    # ✅ 신규 진입 손절: ATR 기반 보정 (변동성 반영)
    atr14 = float(last["ATR14"]) if "ATR14" in last and not np.isnan(last["ATR14"]) else None
    if holding_type == "신규 진입 검토" and buy_low is not None and atr14 is not None and atr14 > 0:
        sl0 = max(0.01, float(buy_low) - 1.0 * atr14)
        sl1 = max(0.01, float(buy_low) - 1.8 * atr14)
    elif holding_type == "신규 진입 검토" and buy_low is not None:
        # ATR이 없으면 최소한의 fallback
        sl0 = buy_low * 0.97
        sl1 = buy_low * 0.94

    levels_dict = {
        "buy_low": buy_low, "buy_high": buy_high,
        "tp0": tp0, "tp1": tp1, "tp2": tp2,
        "sl0": sl0, "sl1": sl1,
    }

    # ✅ 상태 머신
    state_name, action_text, recover_level, phase = analysis.compute_state_and_action(
        holding_type=holding_type,
        price_now=price_now,
        avg_price=avg_price,
        levels=levels_dict,
        last_row=last,
    )

    # ✅ 구조 붕괴 플래그 (UI에서 레벨 무효화/숨김 처리)
    structure_broken = ("구조 붕괴" in state_name)

    rr = analysis.calc_rr_ratio(price_now, tp1, sl0)

    bias_comment = analysis.short_term_bias(last)
    gap_pct, gap_comment = analysis.calc_gap_info(df)
    price_move_abs = abs(float(last["Close"]) - float(last["Open"])) if atr14 is not None else None

    vp_levels = analysis.get_volume_profile(df)
    heavy_days = analysis.get_heavy_days(df)
    intraday_sc, intraday_comment = analysis.get_intraday_5m_score(df_5m)

    score_mkt, _, _ = market.compute_market_score(ov)
    alerts = analysis.build_risk_alerts(score_mkt, last, gap_pct, atr14, price_move_abs)

    is_fav = symbol in st.session_state["favorite_symbols"]
    fav_new = st.checkbox("⭐ 이 종목 즐겨찾기", value=is_fav)
    if fav_new and not is_fav:
        st.session_state["favorite_symbols"].append(symbol)
    elif (not fav_new) and is_fav:
        st.session_state["favorite_symbols"].remove(symbol)

    # 스크롤(분석하기 눌렀을 때만)
    st.markdown('<div id="analysis_result_anchor"></div>', unsafe_allow_html=True)
    if st.session_state.get("scroll_to_result", False):
        st.markdown(
            """
            <script>
              setTimeout(function () {
                var el = document.getElementById("analysis_result_anchor");
                if (el) { el.scrollIntoView({behavior: "smooth", block: "start"}); }
              }, 250);
            </script>
            """,
            unsafe_allow_html=True,
        )
        st.session_state["scroll_to_result"] = False

    col_close1, col_close2 = st.columns([1, 6])
    with col_close1:
        if st.button("🧹 결과 닫기", key="close_result"):
            st.session_state["show_result"] = False
            st.session_state["analysis_params"] = None
            st.success("결과를 닫았습니다.")
            st.rerun()
    with col_close2:
        st.caption("※ 결과는 닫기 전까지 화면에 유지됩니다. (AI 버튼 눌러도 안 닫힘)")

    st.subheader("🧾 요약")
    st.write(f"- 입력 종목: **{display_name}** → 실제 티커: **{symbol}**")
    if fgi is not None:
        st.write(f"- 공포·탐욕지수(FGI, CNN): **{fgi:.1f}**")
    else:
        st.write("- 공포·탐욕지수(FGI): 조회 실패 → 시장심리는 제외하고 지표만 사용")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("일봉 종가(레벨 계산 기준)", f"{price_close:.2f} USD")
        st.metric("현재가(시외 포함, 상태 전환 기준)", f"{price_now:.2f} USD")
        if ext_price is not None:
            diff_pct = (price_now - price_close) / price_close * 100
            sign = "+" if diff_pct >= 0 else ""
            st.caption(f"시외 포함 변화: {sign}{diff_pct:.2f}%")

    with col_b:
        st.markdown(
            f"""
            <div class="card-soft-sm">
              <div class="small-muted">MODE</div>
              <div style="font-size:1.05rem;font-weight:600;">{cfg['name']} 모드</div>
              <div class="small-muted">레벨 계산: 일봉(스윙) · 상태 전환: 현재가(시외 포함)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_c:
        st.markdown(
            f"""
            <div class="card-soft-sm">
              <div class="small-muted">STATUS</div>
              <div>보유 상태: <b>{holding_type}</b></div>
              <div class="small-muted">현재 상태: <b>{state_name}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if holding_type == "보유 중" and avg_price > 0:
        st.write(f"- 평단가: **{avg_price:.2f} USD**")
        st.write(f"- (현재가 기준) 수익률: **{profit_pct:.2f}%**")

    if holding_type == "보유 중" and shares > 0 and avg_price > 0:
        rate = market.get_usdkrw_rate()
        cost_factor = 1 - commission_pct / 100
        total_pnl_after_fee = total_pnl * cost_factor
        pnl_krw = total_pnl_after_fee * rate
        st.write(
            f"- 평가손익(수수료 {commission_pct:.2f}% 반영): "
            f"**{total_pnl_after_fee:,.2f} USD** (약 **{pnl_krw:,.0f} KRW**, 환율 {rate:,.2f}원 기준)"
        )

    st.subheader("🎯 매매 판단 (핵심)")
    col_sig1, col_sig2 = st.columns([2, 1])
    with col_sig1:
        st.write(f"**현재 상태:** ✅ {state_name}")
        st.write(f"**행동지침:** ⭐ {action_text} ⭐")
        st.write(f"**단기 흐름(일봉 기준):** {bias_comment}")
        if recover_level is not None and structure_broken:
            st.caption(f"🔁 회복 확인가(재평가 기준): **{recover_level:.2f}** 위 복귀")

    with col_sig2:
        if rr is not None and (not structure_broken):
            st.metric("손익비 (TP=1차 목표 / SL=0차 손절)", f"{rr:.2f} : 1")
            if rr >= 1.5:
                st.caption("👉 기술적 기준 손익비 양호")
            elif rr <= 1.0:
                st.caption("⚠ 손익비 불리 (손절폭이 상대적으로 큼)")
        else:
            st.caption("손익비는 구조 붕괴/레벨 무효화 구간에서는 의미가 낮아 표시를 생략합니다.")

    st.subheader("📌 가격 레벨 (일봉 기반 가이드)")

    # ✅ 구조 붕괴면 레벨(1차/목표) 표시를 아예 숨김
    if structure_broken:
        st.warning("⚠ 구조가 깨진 상태로 판단되어, 기존 1차/2차/목표 레벨은 **무효화** 처리했습니다.")
        if sl0 is not None:
            st.write(f"- 중단/방어 기준(0차): **{sl0:.2f} USD**")
        if sl1 is not None:
            st.write(f"- 최종 방어선(1차): **{sl1:.2f} USD**")
        if recover_level is not None:
            st.write(f"- 회복 확인가(재평가 기준): **{recover_level:.2f} USD**")
    else:
        if holding_type == "보유 중":
            if buy_low is not None and buy_high is not None:
                st.write(f"- 눌림 매수/유지 관심 구간: **{buy_low:.2f} ~ {buy_high:.2f} USD**")
            if tp0 is not None:
                st.write(f"- 0차 익절(부분): **{tp0:.2f} USD**")
            if tp1 is not None:
                st.write(f"- 1차 목표(주요 저항): **{tp1:.2f} USD**")
            if tp2 is not None:
                st.write(f"- 2차 목표(확장): **{tp2:.2f} USD**")
            if sl0 is not None:
                st.write(f"- 0차 방어선: **{sl0:.2f} USD**")
            if sl1 is not None:
                st.write(f"- 최종 방어선: **{sl1:.2f} USD**")
        else:
            if buy_low is not None and buy_high is not None:
                st.write(f"- 1차 시작(분할): **{buy_low:.2f} ~ {buy_high:.2f} USD**")
            if sl0 is not None:
                st.write(f"- 진입 실패(중단 기준): **{sl0:.2f} USD**")
            if sl1 is not None:
                st.write(f"- 최종 방어선: **{sl1:.2f} USD**")
            if recover_level is not None:
                st.write(f"- 회복 확인가(재진입 재평가): **{recover_level:.2f} USD**")

    st.subheader("📊 갭 · 변동성 · 장중 흐름")
    col_gap, col_atr, col_intra = st.columns(3)
    with col_gap:
        if gap_pct is not None:
            st.metric("전일 대비 갭(시가 기준)", f"{gap_pct:.2f}%")
            st.caption(gap_comment)
        else:
            st.caption("갭 정보 계산 불가(데이터 부족)")

    with col_atr:
        if atr14 is not None:
            st.metric("ATR(14, 일봉)", f"{atr14:.2f}")
            if price_move_abs is not None and atr14 > 0:
                ratio = price_move_abs / atr14
                st.caption(f"오늘 일봉 몸통 크기: ATR의 {ratio:.2f}배")
        else:
            st.caption("ATR 계산 불가(데이터 부족)")

    with col_intra:
        if intraday_sc is not None:
            st.metric("장중 흐름 스코어 (0~4)", f"{intraday_sc}")
            st.caption(intraday_comment)
        else:
            st.caption(intraday_comment)

    st.subheader("🏗 매물대(최근 20일) & 큰손 추정 구간")
    col_vp1, col_vp2 = st.columns(2)
    with col_vp1:
        if vp_levels:
            st.markdown("**주요 매물대 (가격대별 거래량 상위)**")
            for lv in vp_levels:
                st.write(
                    f"- **{lv['low']:.2f} ~ {lv['high']:.2f} USD** (중심 {lv['mid']:.2f}) – 거래량 많은 구간"
                )
        else:
            st.caption("매물대 분석 데이터 부족")

    with col_vp2:
        if heavy_days:
            st.markdown("**큰손 추정 구간 (거래량 상위 일자)**")
            for h in heavy_days:
                st.write(f"- {h['date']} 종가 **{h['close']:.2f} USD** – 거래량 상위일")
        else:
            st.caption("거래량 상위 일자 추출 어려움")

    st.subheader("⚠ 리스크 경고 체크리스트")
    for a in alerts:
        st.write(a)

    # =====================================
    # 🤖 AI 해석 (구조 붕괴면 회복 중심으로 더 강하게 유도)
    # =====================================
    st.subheader("🤖 AI 해석")
    st.caption("※ AI는 '확정 매수/매도 지시'가 아니라, 현재가 기준의 '조건부 행동지침'만 제공합니다.")

    try:
        cache_key = ai._ai_make_cache_key(symbol, holding_type, mode_name, avg_price, last, label_mkt, state_name, price_now)
    except Exception:
        cache_key = None

    cached = (cache_key is not None and cache_key in st.session_state.get("ai_cache", {}))
    btn_label = "🔁 AI 해석 다시 생성" if cached else "✨ AI 해석 보기"

    if cache_key is not None:
        st.button(
            btn_label,
            key=f"ai_btn_{cache_key}",
            on_click=ai.request_ai_generation,
            args=(cache_key,),
        )
    else:
        st.info("AI 캐시 키 생성 실패(데이터 부족).")

    if st.session_state.get("ai_request", False) and st.session_state.get("ai_request_key") == cache_key:
        st.session_state["ai_request"] = False
        st.session_state["ai_request_key"] = None

        extra_notes = [
            f"시장점수: {score_mkt} / label: {label_mkt}",
            f"현재상태: {state_name}",
            f"행동지침: {action_text}",
            f"단기흐름(일봉): {bias_comment}",
            f"갭: {gap_comment}",
            f"구조붕괴: {structure_broken}",
        ]

        if holding_type == "보유 중" and avg_price > 0:
            extra_notes.append(f"평단 대비(현재가): {(price_now/avg_price-1)*100:+.2f}%")
        if atr14 is not None:
            extra_notes.append(f"ATR14: {atr14:.2f}")

        # ✅ 구조 붕괴면 levels도 최소화해서 AI가 헷갈리게 말 못 하게 함
        levels_for_ai = levels_dict | {"recover": recover_level}
        if structure_broken:
            levels_for_ai = {
                "sl0": levels_dict.get("sl0"),
                "sl1": levels_dict.get("sl1"),
                "recover": recover_level,
            }

        with st.spinner("AI 해석 생성 중..."):
            ai_model_name = st.session_state.get("ai_model_name", "gpt-4o-mini")
            parsed, err = ai.ai_summarize_and_explain(
                symbol=symbol,
                holding_type=holding_type,
                mode_name=mode_name,
                market_label=label_mkt,
                market_detail=detail_mkt,
                live_price=price_now,
                day_close=price_close,
                avg_price=avg_price,
                state_name=state_name,
                action_text=action_text,
                bias_comment=bias_comment,
                gap_comment=gap_comment,
                rr=rr if (not structure_broken) else None,
                levels=levels_for_ai,
                last_row=last,
                extra_notes=extra_notes,
                model_name=ai_model_name,
            )

        if parsed:
            if cache_key:
                st.session_state["ai_cache"][cache_key] = parsed
            st.success("AI 해석 생성 완료!")
        else:
            st.error(err or "AI 생성 실패")

    ai_out = None
    if cache_key and cache_key in st.session_state.get("ai_cache", {}):
        ai_out = st.session_state.get("ai_cache")[cache_key]

    if ai_out is not None:
        one = str(ai_out.get("summary_one_line", "")).strip()
        blocks = ai_out.get("confusion_explain", [])

        if one:
            st.markdown(
                f"""
                <div class="card-soft">
                  <div class="layer-title-en">AI SUMMARY</div>
                  <div style="font-size:1.05rem;font-weight:700;line-height:1.35;">{one}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if isinstance(blocks, list) and blocks:
            blocks = blocks[:2]
            cols = st.columns(len(blocks))
            for i, b in enumerate(blocks):
                title = str(b.get("title", "")).strip()
                desc = str(b.get("desc", "")).strip()
                with cols[i]:
                    st.markdown(
                        f"""
                        <div class="card-soft-sm">
                          <div style="font-weight:700;margin-bottom:6px;">{title}</div>
                          <div class="small-muted" style="line-height:1.45;">{desc}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
    else:
        st.info("AI 해석은 버튼을 누를 때만 생성됩니다. (Streamlit Secrets에 OPENAI_API_KEY 필요)")

    st.subheader("📈 가격/볼린저밴드 차트 (일봉 기반)")
    chart_df = df[["Close", "MA20", "BBL", "BBU"]].tail(120)
    st.line_chart(chart_df)
