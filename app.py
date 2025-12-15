 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/app.py b/app.py
index bf895d24a8f64fbc61f3a89ad86a41519b218ef7..47c0fe034218aa52eda657622cbc1f37dfccb4e5 100644
--- a/app.py
+++ b/app.py
@@ -1,41 +1,50 @@
 import streamlit as st
 import yfinance as yf
 import pandas as pd
 import numpy as np
 import requests
 
 # 선택 기능: AI 해석(요약/헷갈림 설명)
 try:
     from openai import OpenAI
 except Exception:
     OpenAI = None
 import os
 import json
 import re
 import hashlib
 
+# 기본 AI 모델 설정 (환경변수 또는 secrets에서 읽기)
+try:
+    ai_model_name = st.secrets.get("AI_MODEL_NAME", os.getenv("AI_MODEL_NAME"))
+except Exception:
+    ai_model_name = os.getenv("AI_MODEL_NAME")
+
+if not ai_model_name:
+    ai_model_name = "gpt-4o-mini"
+
 
 # =====================================
 # 페이지 설정
 # =====================================
 st.set_page_config(
     page_title="내 주식 자동판독기 (시장 개요 + 레이어/갭/ATR/장중 흐름)",
     page_icon="📈",
     layout="wide",
 )
 
 # =====================================
 # 전체 스타일 (라이트 + 모바일 가독성 강화)
 # =====================================
 st.markdown(
     """
 <style>
 @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
 
 html, body, [data-testid="stAppViewContainer"] {
     font-family: "Pretendard", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
     color: #111827;
     background-color: #ffffff;
     color-scheme: light;
     -webkit-text-size-adjust: 100% !important;
 }
@@ -1686,143 +1695,141 @@ with col_main:
 
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
 
-    
-        # =====================================
-        # 🤖 AI 해석 (요약 + 헷갈림 설명)
-        # =====================================
-        st.subheader("🤖 AI 해석")
-        st.caption("※ AI는 '확정 매수/매도 지시'가 아니라, 현재 신호가 왜 그렇게 보이는지(해석/설명)만 제공합니다.")
-
-        try:
-            cache_key = _ai_make_cache_key(symbol, holding_type, mode_name, avg_price, last, label_mkt)
-        except Exception:
-            cache_key = None
-
-        cached = (cache_key is not None and cache_key in st.session_state.get("ai_cache", {}))
-
-        btn_label = "🔁 AI 해석 다시 생성" if cached else "✨ AI 해석 보기"
-
-        # 버튼 클릭 시 rerun되면서 화면이 맨 위로 올라가는 문제를 막기 위해:
-        # 1) 클릭 상태를 session_state에 저장
-        # 2) 결과 앵커로 자동 스크롤
-        st.button(
-            btn_label,
-            key=f"ai_btn_{symbol}_{holding_type}_{mode_name}",
-            on_click=request_ai_generation,
-        )
+    # =====================================
+    # 🤖 AI 해석 (요약 + 헷갈림 설명)
+    # =====================================
+    st.subheader("🤖 AI 해석")
+    st.caption("※ AI는 '확정 매수/매도 지시'가 아니라, 현재 신호가 왜 그렇게 보이는지(해석/설명)만 제공합니다.")
 
-        # 버튼을 눌렀을 때만 실제 AI 호출 (session_state 기반)
-        if st.session_state.get("ai_request", False):
-            st.session_state["ai_request"] = False  # 중복 호출 방지(바로 해제)
-
-            levels_dict = {
-                "buy_low": buy_low, "buy_high": buy_high,
-                "tp0": tp0, "tp1": tp1, "tp2": tp2,
-                "sl0": sl0, "sl1": sl1,
-            }
-
-            # 보유/신규에 따라 '헷갈림' 포인트를 다르게 구성 (프롬프트에서 분기)
-            extra_notes = [
-                f"시장점수: {score_mkt} / label: {label_mkt}",
-                f"신호: {signal}",
-                f"단기흐름: {bias_comment}",
-                f"갭: {gap_comment}",
-            ]
-            if rr is not None:
-                extra_notes.append(f"손익비(RR): {rr:.2f}:1")
-            if holding_type == "보유 중" and avg_price > 0:
-                extra_notes.append(f"평단 대비: {(price/avg_price-1)*100:+.2f}%")
-            if gap_pct is not None:
-                extra_notes.append(f"갭%: {gap_pct:+.2f}%")
-            if atr14 is not None:
-                extra_notes.append(f"ATR14: {atr14:.2f}")
-
-            with st.spinner("AI 해석 생성 중..."):
-                parsed, err = ai_summarize_and_explain(
-                    symbol=symbol,
-                    holding_type=holding_type,
-                    mode_name=mode_name,
-                    market_label=label_mkt,
-                    market_detail=detail_mkt,
-                    price=price,
-                    avg_price=avg_price,
-                    signal=signal,
-                    bias_comment=bias_comment,
-                    gap_comment=gap_comment,
-                    rr=rr,
-                    levels=levels_dict,
-                    last_row=last,
-                    extra_notes=extra_notes,
-                    model_name=ai_model_name,
-                )
-            if parsed:
-                if cache_key:
-                    st.session_state["ai_cache"][cache_key] = parsed
-                st.success("AI 해석 생성 완료!")
-            else:
-                st.error(err or "AI 생성 실패")
-
-if cache_key and cache_key in st.session_state.get("ai_cache", {}):
-    ai_out = st.session_state["ai_cache"][cache_key]
-    one = ai_out.get("summary_one_line", "").strip()
-    blocks = ai_out.get("confusion_explain", [])
-
-    st.markdown(
-        f"""
-        <div class="card-soft">
-          <div class="layer-title-en">AI SUMMARY</div>
-          <div style="font-size:1.05rem;font-weight:700;line-height:1.35;">{one}</div>
-        </div>
-        """,
-        unsafe_allow_html=True,
-    )
+    try:
+        cache_key = _ai_make_cache_key(symbol, holding_type, mode_name, avg_price, last, label_mkt)
+    except Exception:
+        cache_key = None
 
-    if isinstance(blocks, list) and blocks:
-        blocks = blocks[:2]
-        cols = st.columns(len(blocks))
-        for i, b in enumerate(blocks):
-            title = str(b.get("title", "")).strip()
-            desc = str(b.get("desc", "")).strip()
-            with cols[i]:
-                st.markdown(
-                    f"""
-                    <div class="card-soft-sm">
-                      <div style="font-weight:700;margin-bottom:6px;">{title}</div>
-                      <div class="small-muted" style="line-height:1.45;">{desc}</div>
-                    </div>
-                    """,
-                    unsafe_allow_html=True,
-                )
+    cached = (cache_key is not None and cache_key in st.session_state.get("ai_cache", {}))
+
+    btn_label = "🔁 AI 해석 다시 생성" if cached else "✨ AI 해석 보기"
 
-else:  # ✅ 이 else는 위 if(cache_key...)의 else
-    st.info(
-        "AI 해석은 버튼을 누를 때만 생성됩니다. "
-        "(Streamlit Secrets에 OPENAI_API_KEY가 있어야 합니다.)"
+    # 버튼 클릭 시 rerun되면서 화면이 맨 위로 올라가는 문제를 막기 위해:
+    # 1) 클릭 상태를 session_state에 저장
+    # 2) 결과 앵커로 자동 스크롤
+    st.button(
+        btn_label,
+        key=f"ai_btn_{symbol}_{holding_type}_{mode_name}",
+        on_click=request_ai_generation,
     )
 
+    # 버튼을 눌렀을 때만 실제 AI 호출 (session_state 기반)
+    if st.session_state.get("ai_request", False):
+        st.session_state["ai_request"] = False  # 중복 호출 방지(바로 해제)
+
+        levels_dict = {
+            "buy_low": buy_low, "buy_high": buy_high,
+            "tp0": tp0, "tp1": tp1, "tp2": tp2,
+            "sl0": sl0, "sl1": sl1,
+        }
+
+        # 보유/신규에 따라 '헷갈림' 포인트를 다르게 구성 (프롬프트에서 분기)
+        extra_notes = [
+            f"시장점수: {score_mkt} / label: {label_mkt}",
+            f"신호: {signal}",
+            f"단기흐름: {bias_comment}",
+            f"갭: {gap_comment}",
+        ]
+        if rr is not None:
+            extra_notes.append(f"손익비(RR): {rr:.2f}:1")
+        if holding_type == "보유 중" and avg_price > 0:
+            extra_notes.append(f"평단 대비: {(price/avg_price-1)*100:+.2f}%")
+        if gap_pct is not None:
+            extra_notes.append(f"갭%: {gap_pct:+.2f}%")
+        if atr14 is not None:
+            extra_notes.append(f"ATR14: {atr14:.2f}")
+
+        with st.spinner("AI 해석 생성 중..."):
+            parsed, err = ai_summarize_and_explain(
+                symbol=symbol,
+                holding_type=holding_type,
+                mode_name=mode_name,
+                market_label=label_mkt,
+                market_detail=detail_mkt,
+                price=price,
+                avg_price=avg_price,
+                signal=signal,
+                bias_comment=bias_comment,
+                gap_comment=gap_comment,
+                rr=rr,
+                levels=levels_dict,
+                last_row=last,
+                extra_notes=extra_notes,
+                model_name=ai_model_name,
+            )
+        if parsed:
+            if cache_key:
+                st.session_state["ai_cache"][cache_key] = parsed
+            st.success("AI 해석 생성 완료!")
+        else:
+            st.error(err or "AI 생성 실패")
+
+    if cache_key and cache_key in st.session_state.get("ai_cache", {}):
+        ai_out = st.session_state["ai_cache"][cache_key]
+        one = ai_out.get("summary_one_line", "").strip()
+        blocks = ai_out.get("confusion_explain", [])
+
+        st.markdown(
+            f"""
+            <div class="card-soft">
+              <div class="layer-title-en">AI SUMMARY</div>
+              <div style="font-size:1.05rem;font-weight:700;line-height:1.35;">{one}</div>
+            </div>
+            """,
+            unsafe_allow_html=True,
+        )
+
+        if isinstance(blocks, list) and blocks:
+            blocks = blocks[:2]
+            cols = st.columns(len(blocks))
+            for i, b in enumerate(blocks):
+                title = str(b.get("title", "")).strip()
+                desc = str(b.get("desc", "")).strip()
+                with cols[i]:
+                    st.markdown(
+                        f"""
+                        <div class="card-soft-sm">
+                          <div style="font-weight:700;margin-bottom:6px;">{title}</div>
+                          <div class="small-muted" style="line-height:1.45;">{desc}</div>
+                        </div>
+                        """,
+                        unsafe_allow_html=True,
+                    )
+
+    else:  # ✅ 이 else는 위 if(cache_key...)의 else
+        st.info(
+            "AI 해석은 버튼을 누를 때만 생성됩니다. "
+            "(Streamlit Secrets에 OPENAI_API_KEY가 있어야 합니다.)"
+        )
 
-        st.subheader("📈 가격/볼린저밴드 차트 (단순 표시)")
-        chart_df = df[["Close", "MA20", "BBL", "BBU"]].tail(120)
-        st.line_chart(chart_df)
+    st.subheader("📈 가격/볼린저밴드 차트 (단순 표시)")
+    chart_df = df[["Close", "MA20", "BBL", "BBU"]].tail(120)
+    st.line_chart(chart_df)
 
EOF
)
