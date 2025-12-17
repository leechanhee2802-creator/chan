"""AI integration helpers for generating summaries."""

import hashlib
import json
import os
import re

import streamlit as st

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None


def _ai_make_cache_key(symbol: str, holding_type: str, mode_name: str, avg_price: float, df_last, market_label: str,
state_name: str, live_price: float):
    payload = {
        "symbol": symbol,
        "holding_type": holding_type,
        "mode": mode_name,
        "avg_price": round(float(avg_price or 0.0), 4),
        "live_price": round(float(live_price or 0.0), 4),
        "close": round(float(df_last.get("Close", 0.0)), 4),
        "ma20": round(float(df_last.get("MA20", 0.0)), 4),
        "bbl": round(float(df_last.get("BBL", 0.0)), 4),
        "bbu": round(float(df_last.get("BBU", 0.0)), 4),
        "rsi": round(float(df_last.get("RSI14", 0.0)), 4),
        "macd": round(float(df_last.get("MACD", 0.0)), 4),
        "macds": round(float(df_last.get("MACD_SIGNAL", 0.0)), 4),
        "state": state_name,
        "market": market_label,
    }
    s = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def _ai_extract_json(text: str):
    if not text:
        return None
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def ai_summarize_and_explain(
    symbol: str,
    holding_type: str,
    mode_name: str,
    market_label: str,
    market_detail: str,
    live_price: float,
    day_close: float,
    avg_price: float,
    state_name: str,
    action_text: str,
    bias_comment: str,
    gap_comment: str,
    rr: float,
    levels: dict,
    last_row,
    extra_notes: list,
    model_name: str = "gpt-4o-mini",
):
    if OpenAI is None:
        return None, "openai 패키지를 찾지 못했습니다. requirements.txt에 openai를 추가했는지 확인하세요."
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None, "OPENAI_API_KEY 환경변수가 비어 있습니다. Streamlit Cloud → Settings → Secrets에 설정하세요."

    client = OpenAI(api_key=api_key)

    compact = {
        "symbol": symbol,
        "holding_type": holding_type,
        "mode": mode_name,
        "market": {"label": market_label, "detail": market_detail},
        "price_now": live_price,
        "price_day_close": day_close,
        "avg_price": avg_price,
        "levels": levels,
        "state": state_name,
        "action": action_text,
        "bias": bias_comment,
        "gap": gap_comment,
        "rr": rr,
        "extra_notes": extra_notes,
        "last_row": {
            "close": float(last_row.get("Close", 0.0)),
            "ma20": float(last_row.get("MA20", 0.0)),
            "ma5": float(last_row.get("MA5", 0.0)),
            "bbl": float(last_row.get("BBL", 0.0)),
            "bbu": float(last_row.get("BBU", 0.0)),
            "rsi": float(last_row.get("RSI14", 0.0)),
            "macd": float(last_row.get("MACD", 0.0)),
            "macds": float(last_row.get("MACD_SIGNAL", 0.0)),
            "stoch_k": float(last_row.get("STOCH_K", 0.0)),
            "stoch_d": float(last_row.get("STOCH_D", 0.0)),
            "atr14": float(last_row.get("ATR14", 0.0)),
        },
    }

    instruction = (
        "현재 가격/시장 상태를 기반으로 조건부 행동지침을 JSON 형식으로 제공해 주세요. "
        "summary_one_line(문장 하나)와 confusion_explain(2개 블록)을 포함해야 합니다."
    )

    system = (
        "너는 트레이딩 보조 AI야. 데이터 기반으로 명료한 조언을 해줘."
        "JSON만 반환해."
    )
    user = json.dumps({"instruction": instruction, "compact": compact}, ensure_ascii=False)

    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.15,
        )
        text = (resp.choices[0].message.content or "").strip()
        parsed = _ai_extract_json(text)
        if parsed and isinstance(parsed.get("summary_one_line"), str) and isinstance(parsed.get("confusion_explain"), list):
            if len(parsed["confusion_explain"]) >= 2:
                return parsed, None
            return None, "AI 응답이 너무 짧습니다(설명 블록 부족)."
        return None, "AI 응답에서 JSON 파싱 실패 (모델이 형식을 어겼습니다)."
    except Exception as e:
        return None, f"AI 호출 실패: {e}"


def request_ai_generation(cache_key: str):
    st.session_state["ai_request_key"] = cache_key
    st.session_state["ai_request"] = True
