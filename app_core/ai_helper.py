import os, json, re, hashlib
import streamlit as st

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

def _ai_make_cache_key(symbol: str, holding_type: str, mode_name: str, avg_price: float, df_last, market_label: str, state_name: str, live_price: float):
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

def request_ai_generation(cache_key: str):
    st.session_state["ai_request_key"] = cache_key
    st.session_state["ai_request"] = True

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
    rr,
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
        "state": state_name,
        "action": action_text,
        "rr_ratio": rr,
        "levels": levels,
        "indicators": {
            "MA20": float(last_row["MA20"]),
            "BBL": float(last_row["BBL"]),
            "BBU": float(last_row["BBU"]),
            "RSI14": float(last_row["RSI14"]),
            "MACD": float(last_row["MACD"]),
            "MACD_SIGNAL": float(last_row["MACD_SIGNAL"]),
            "ATR14": float(last_row["ATR14"]),
        },
        "notes": extra_notes[:10],
        "trend_hint": bias_comment,
        "gap_hint": gap_comment,
    }

    system = (
        "너는 '주식 자동판독기'의 해석 도우미다. "
        "확정 매수/매도 지시를 하지 말고, "
        "대신 '가격 기준의 조건부 행동지침'을 아주 직관적으로 정리한다. "
        "영어/전문용어(MA20, MACD 등)는 가능하면 쓰지 말고, 필요하면 '20일선'처럼 한국어로 짧게만 언급한다. "
        "반드시 JSON만 출력한다."
    )

    if holding_type == "보유 중":
        title2 = "보유자 관점: 지금 유지/축소 판단 포인트"
        desc2 = "평단/손절선/목표가 기준으로 '지금 어떤 가격에서 무엇을 하면 되는지'를 2~3줄로 정리"
    else:
        title2 = "신규진입 관점: 지금 들어가도 되는지 체크"
        desc2 = "1차/2차 진입가, 진입 실패가(중단), 회복 확인가(재평가 조건)를 가격으로 2~3줄 정리"

    user = (
        "아래 데이터는 기술적 지표 기반의 요약 데이터다.\n"
        "반드시 아래 JSON 형태로만 출력해라(키/구조/타입 고정).\n\n"
        "{\n"
        "  \"summary_one_line\": \"지금 상태(state) + 현재가(price_now) 기준으로, 딱 한 문장 행동지침(가격조건 포함)\",\n"
        "  \"confusion_explain\": [\n"
        "    {\n"
        "      \"title\": \"지금 가장 안전한 행동(가격 기준)\",\n"
        "      \"desc\": \"반드시 price_now + 레벨(buy/tp/sl/recover 중 2개 이상)을 직접 숫자로 언급해서, 2~4문장으로 행동지침\"\n"
        "    },\n"
        "    {\n"
        f"      \"title\": \"{title2}\",\n"
        f"      \"desc\": \"{desc2}. 반드시 숫자 레벨 2개 이상 포함\"\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        "제약:\n"
        "- '지금 사라/팔아라' 같은 확정 지시는 금지.\n"
        "- 대신 'XX 밑이면 중단/방어', 'YY 위면 확인 후 접근' 같은 조건부 문장으로.\n"
        "- 한국어 위주. 영어/전문용어는 최소.\n"
        "- JSON 외 텍스트 출력 금지.\n\n"
        f"DATA:\n{json.dumps(compact, ensure_ascii=False)}"
    )

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
