import streamlit as st
import pandas as pd
import numpy as np
import requests
from app_core import analysis

# 선택 기능: AI 해석(요약/헷갈림 설명)
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

import os
import json
import re
import hashlib


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

[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #f4f7ff 0%, #eefdfd 50%, #fdfcfb 100%);
}

main.block-container {
    max-width: 1250px;
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}

header, [data-testid="stHeader"], [data-testid="stSidebar"] {
    background-color: #ffffff !important;
}

[data-testid="stExpander"],
[data-testid="stExpander"] > details,
[data-testid="stExpander"] details > summary,
[data-testid="stExpander"] details > div {
    background-color: #ffffff !important;
    color: #111827 !important;
}

/* 제목들 */
h1 { font-size: 1.6rem; font-weight: 700; color: #111827 !important; }
h2 { font-size: 1.25rem; font-weight: 600; color: #111827 !important; }
h3 { font-size: 1.05rem; font-weight: 600; color: #111827 !important; }

/* 기본 텍스트 */
p, label, span, div { font-size: 0.94rem; color: #111827 !important; }

.small-muted { font-size: 0.8rem; color: #6b7280 !important; }

/* 공통 카드 */
.card-soft {
    background: rgba(255, 255, 255, 0.96);
    border-radius: 20px;
    padding: 14px 18px;
    box-shadow: 0 10px 25px rgba(15, 23, 42, 0.08);
    border: 1px solid #e5e7eb;
    margin-bottom: 12px;
}
.card-soft-sm {
    background: rgba(255, 255, 255, 0.96);
    border-radius: 18px;
    padding: 10px 14px;
    box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
    border: 1px solid #e5e7eb;
    margin-bottom: 10px;
}

/* 칩 */
.chip {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.84rem;
    font-weight: 600;
}
.chip-green { background: #bbf7d0; color: #166534 !important; }
.chip-blue  { background: #dbeafe; color: #1d4ed8 !important; }
.chip-red   { background: #fee2e2; color: #b91c1c !important; }

/* 레이어 */
.layer-title-en {
    font-size: 0.85rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #6b7280 !important;
    margin-bottom: 4px;
}
.layer-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 4px;
}
.layer-symbol { font-weight: 600; font-size: 0.95rem; color: #111827 !important; }
.layer-chg-pos { font-weight: 600; font-size: 0.95rem; color: #dc2626 !important; } /* 빨강 */
.layer-chg-neg { font-weight: 600; font-size: 0.95rem; color: #2563eb !important; } /* 파랑 */
.layer-chg-flat{ font-weight: 600; font-size: 0.95rem; color: #4b5563 !important; }

/* metric 카드 */
.metric-card {
    background: rgba(255, 255, 255, 0.96);
    border-radius: 20px;
    padding: 12px 16px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
    margin-bottom: 8px;
}
.metric-label { font-size: 0.8rem; font-weight: 500; color: #6b7280 !important; }
.metric-value { font-size: 1.3rem; font-weight: 700; margin-top: 4px; color: #111827 !important; }
.metric-delta-pos {
    display: inline-flex; align-items: center;
    margin-top: 6px; padding: 2px 8px; border-radius: 999px;
    background: #bbf7d0; color: #166534 !important;
    font-size: 0.78rem; font-weight: 600;
}
.metric-delta-neg {
    display: inline-flex; align-items: center;
    margin-top: 6px; padding: 2px 8px; border-radius: 999px;
    background: #fee2e2; color: #b91c1c !important;
    font-size: 0.78rem; font-weight: 600;
}

/* 입력 박스 */
[data-baseweb="input"] > div,
[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    border-radius: 999px !important;
    border: 1px solid #e5e7eb !important;
}
[data-baseweb="input"] input, textarea { background-color: transparent !important; color: #111827 !important; }
textarea { border-radius: 16px !important; }
input::placeholder, textarea::placeholder { color: #9ca3af !important; }

[data-baseweb="radio"] > label { background-color: transparent !important; color: #111827 !important; }
button[role="tab"] > div { color: #111827 !important; }

.stButton>button {
    border-radius: 999px;
    padding: 6px 16px;
    border: 1px solid #e5e7eb;
    background: #ffffff;
    font-size: 0.92rem;
    font-weight: 500;
    color: #111827 !important;
}
.stButton>button:hover {
    border-color: #4f46e5;
    background: #eef2ff;
}

[data-testid="stDataFrame"], [data-testid="stTable"] { background-color: #ffffff; }

@media (max-width: 768px) {
    .metric-value { font-size: 1.4rem; }
    .layer-symbol, .layer-chg-pos, .layer-chg-neg, .layer-chg-flat { font-size: 1.0rem; }
}

[data-testid="stExpander"] summary { color: #111827 !important; }
</style>
""",
    unsafe_allow_html=True,
)

# =====================================
# 한글 이름 → 티커 매핑
# =====================================
KOREAN_TICKER_MAP = {
    "엔비디아": "NVDA", "엔비디아코퍼레이션": "NVDA",
    "마이크로소프트": "MSFT", "마소": "MSFT",
    "애플": "AAPL",
    "테슬라": "TSLA",
    "아마존": "AMZN", "아마존닷컴": "AMZN",
    "구글": "GOOGL", "알파벳": "GOOGL", "알파벳A": "GOOGL", "알파벳C": "GOOG",
    "메타": "META", "페이스북": "META",
    "넷플릭스": "NFLX",
    "슈퍼마이크로": "SMCI", "슈퍼마이크로컴퓨터": "SMCI",
    "팔란티어": "PLTR",
    "브로드컴": "AVGO",
    "에이엠디": "AMD", "AMD": "AMD",
    "TSMC": "TSM", "티에스엠씨": "TSM",
    "엔페이즈": "ENPH",
    "코카콜라": "KO", "펩시": "PEP",
    "맥도날드": "MCD", "스타벅스": "SBUX",
    "나이키": "NKE", "월마트": "WMT", "코스트코": "COST",
    "존슨앤존슨": "JNJ", "존슨앤드존슨": "JNJ",
    "화이자": "PFE", "모더나": "MRNA",
    "유나이티드헬스": "UNH", "메르크": "MRK", "애브비": "ABBV",
    "JP모건": "JPM", "제이피모건": "JPM",
    "골드만삭스": "GS", "모건스탠리": "MS",
    "뱅크오브아메리카": "BAC",
    "씨티": "C", "씨티그룹": "C",
    "페이팔": "PYPL",
    "엑슨모빌": "XOM", "셰브론": "CVX",
    "캐터필러": "CAT", "3M": "MMM",
    "허니웰": "HON", "디즈니": "DIS",
    "버라이즌": "VZ", "AT&T": "T",
    "오라클": "ORCL",
    "코인베이스": "COIN", "코인베이스글로벌": "COIN",
    "마이크로스트래티지": "MSTR",
    "리오트": "RIOT", "라이엇": "RIOT",
    "마라톤디지털": "MARA", "마라톤": "MARA",
    "클린스파크": "CLSK",
    "비트팜": "BITF",
    "갤럭시디지털": "BRPHF",
    "QQQ": "QQQ", "나스닥ETF": "QQQ", "나스닥100": "QQQ",
    "SPY": "SPY", "S&P500": "SPY", "SP500": "SPY",
    "VOO": "VOO", "S&P인덱스": "VOO",
    "SOXL": "SOXL", "반도체3배": "SOXL",
    "SOXS": "SOXS", "반도체인버스3배": "SOXS",
    "TQQQ": "TQQQ", "나스닥3배": "TQQQ",
    "SQQQ": "SQQQ", "나스닥인버스3배": "SQQQ",
    "TECL": "TECL", "기술주3배": "TECL",
    "SPXL": "SPXL", "S&P3배": "SPXL",
    "SPXS": "SPXS", "S&P인버스3배": "SPXS",
    "LABU": "LABU", "바이오3배": "LABU",
    "LABD": "LABD", "바이오인버스3배": "LABD",
    "ARKK": "ARKK",
    "비트코인ETF": "IBIT",
    "아이쉐어즈비트코인": "IBIT",
}

POPULAR_SYMBOLS = [
    "NVDA", "META", "TSLA", "AAPL", "MSFT", "AMZN",
    "QQQ", "TQQQ", "SOXL", "SPY", "VOO",
    "COIN", "MSTR", "RIOT", "MARA",
    "ORCL", "PYPL", "NFLX", "PLTR", "AVGO",
]

SCAN_CANDIDATES = sorted(set(
    POPULAR_SYMBOLS + ["NVDA", "AAPL", "MSFT", "AMZN", "META", "GOOGL", "TSLA"]
))

def normalize_symbol(user_input: str) -> str:
    name = (user_input or "").strip()
    if name in KOREAN_TICKER_MAP:
        return KOREAN_TICKER_MAP[name]
    return name.replace(" ", "").upper()

@st.cache_data(ttl=60)
def get_us_market_overview():
    return market.get_us_market_overview()

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

# =========================================================
# 시장 판독(점수) + 장 상태 배지
# =========================================================
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
    n = max(1, len(market.BIGTECH_LIST))
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

# =====================================
# 가격 데이터 + 지표 (레벨 계산은 일봉)
# =====================================
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

def get_intraday_5m(symbol: str):
    try:
        t = yf.Ticker(symbol)
        df = t.history(period="2d", interval="5m", auto_adjust=False, prepost=False)
        if df.empty:
            return pd.DataFrame()
        return df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    except Exception:
        return pd.DataFrame()

# =====================================
# AI 해석 유틸 (상태 머신 반영)
# =====================================
def _ai_make_cache_key(symbol: str, holding_type: str, mode_name: str, avg_price: float, df_last: pd.Series, market_label: str, state_name: str, live_price: float):
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
    last_row: pd.Series,
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
        "price_now": live_price,        # ✅ 상태 전환 기준
        "price_day_close": day_close,    # ✅ 레벨 계산 기준
        "avg_price": avg_price,
        "state": state_name,            # ✅ 상태 머신 결과
        "action": action_text,          # ✅ 앱이 만든 행동지침(가격조건 포함)
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

# ✅ AI 버튼: 결과를 닫지 않게 + 스크롤 강제 안 함
def request_ai_generation(cache_key: str):
    st.session_state["ai_request_key"] = cache_key
    st.session_state["ai_request"] = True

# =====================================
# 코멘트/판단 함수들
# =====================================
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

# =====================================
# ✅ 상태 머신: 구조 붕괴면 레벨 무효화 + 회복만 남김
# =====================================
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

    # 회복 확인가: "매수밴드 상단 회복" vs "20일선 회복" 중 더 보수적(높은 값)
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

    # ✅ 구조 붕괴 판정 (상태 전환은 현재가 기준)
    structure_broken = False
    if price_now is not None and sl1 is not None:
        if price_now < float(sl1) * 0.998:
            structure_broken = True

    # ---- 구조 붕괴면: 기존 1차/목표 전부 무효화, 회복만 표시 ----
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

    # ---- 신규 진입 ----
    if holding_type != "보유 중":
        if price_now is None:
            return "데이터 부족", "현재가(시외 포함)를 못 불러와서 상태 판정 불가", recover_level, "unknown"

        # 진입 실패(약): sl0 하회 (단, 구조 붕괴는 위에서 처리됨)
        if sl0 is not None and price_now < float(sl0) * 0.998:
            return (
                "진입 실패(중단)",
                f"진입 가설이 흔들림. 우선 중단/관망. (회복 확인: {recover_level:.2f} 위 복귀 시 재평가)" if recover_level else
                "진입 가설이 흔들림. 우선 중단/관망. (회복 확인가 재평가 필요)",
                recover_level,
                "fail_soft",
            )

        # 1차 구간 진입
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

    # ---- 보유 중 ----
    else:
        if price_now is None:
            return "데이터 부족", "현재가(시외 포함)를 못 불러와서 상태 판정 불가", recover_level, "unknown"

        # 방어(약)
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

# =====================================
# 매물대/거래량 관련
# =====================================
# =====================================
# 신규 진입 스캐너 (A안: 심플)
# =====================================
def scan_new_entry_candidates(cfg: dict, max_results: int = 8):
    results = []
    ov = get_us_market_overview()
    market_score, _, _ = compute_market_score(ov)

    for sym in SCAN_CANDIDATES:
        df = market.get_price_data(sym, cfg["period"])
        if df.empty:
            continue
        df = analysis.add_indicators(df)
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

        bias = analysis.short_term_bias(last)
        score = 0
        if "상방" in bias:
            score += 2
        elif "중립" in bias:
            score += 1

        score += max(0, 3 - dist_band_pct)
        score += max(0, 2 - abs(rsi - 50) / 10)

        # 스캐너는 단순 RR 유지
        sl0_new = buy_low * 0.97
        rr = analysis.calc_rr_ratio(price_close, tp1, sl0_new)

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
# =====================================
# 세션 상태
# =====================================
if "recent_symbols" not in st.session_state:
    st.session_state["recent_symbols"] = []
if "favorite_symbols" not in st.session_state:
    st.session_state["favorite_symbols"] = []
if "selected_symbol" not in st.session_state:
    st.session_state["selected_symbol"] = "엔비디아"
if "run_from_side" not in st.session_state:
    st.session_state["run_from_side"] = False
if "symbol_input" not in st.session_state:
    st.session_state["symbol_input"] = st.session_state["selected_symbol"]
if "pending_symbol" not in st.session_state:
    st.session_state["pending_symbol"] = ""
if "scroll_to_result" not in st.session_state:
    st.session_state["scroll_to_result"] = False
if "scan_results" not in st.session_state:
    st.session_state["scan_results"] = None

# ✅ 결과 유지용 (AI 클릭 rerun에도 결과 안 닫히게)
if "show_result" not in st.session_state:
    st.session_state["show_result"] = False
if "analysis_params" not in st.session_state:
    st.session_state["analysis_params"] = None

# ✅ AI 캐시/요청 플래그
if "ai_cache" not in st.session_state:
    st.session_state["ai_cache"] = {}
if "ai_request" not in st.session_state:
    st.session_state["ai_request"] = False
if "ai_request_key" not in st.session_state:
    st.session_state["ai_request_key"] = None

# 사이드 클릭 -> 분석 트리거
if st.session_state.get("pending_symbol"):
    ps = st.session_state["pending_symbol"]
    st.session_state["symbol_input"] = ps
    st.session_state["selected_symbol"] = ps
    st.session_state["run_from_side"] = True
    st.session_state["pending_symbol"] = ""

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
            get_us_market_overview.clear()

        with st.spinner("미국 선물 · 금리 · 달러 · ETF · 레이어 상황 불러오는 중..."):
            ov = get_us_market_overview()

        score_mkt, label_mkt, detail_mkt = compute_market_score(ov)

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
            st.markdown('<div class="metric-label">나스닥 선물</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{lastv:.1f}</div>' if lastv is not None else '<div class="metric-value">N/A</div>', unsafe_allow_html=True)
            if chg is not None:
                st.markdown(f'<div class="metric-delta-pos">↑ {chg:.2f}%</div>' if chg >= 0 else f'<div class="metric-delta-neg">↓ {abs(chg):.2f}%</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            lastv = es.get("last")
            chg = es.get("chg_pct")
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">S&P500 선물</div>', unsafe_allow_html=True)
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

        verdict = compute_market_verdict_scores(ov)
        session_badge, session_cls = market_state_badge_from_etfs(etfs)

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
            us10y_chg = rf.get("us10y_chg")
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">미 10년물</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{us10y:.2f}%</div>' if us10y is not None else '<div class="metric-value">N/A</div>', unsafe_allow_html=True)
            if us10y_chg is not None:
                st.markdown(f'<div class="metric-delta-pos">▲ {us10y_chg:.3f}p</div>' if us10y_chg >= 0 else f'<div class="metric-delta-neg">▼ {abs(us10y_chg):.3f}p</div>', unsafe_allow_html=True)
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
            st.markdown('<div class="small-muted">※ 수치는 약간의 지연이 있을 수 있습니다.</div>', unsafe_allow_html=True)
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
            sym = it["symbol"]
            chg = it["chg"]
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
            label = it["label"]
            chg = it["chg"]
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

    cfg = get_mode_config(mode_name)

    prefix = (user_symbol or "").strip().upper().replace(" ", "")
    candidates = sorted(set(POPULAR_SYMBOLS + st.session_state["recent_symbols"]))
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
        cfg = get_mode_config(mode_name)

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
                scan_mkt_score, scan_list = scan_new_entry_candidates(cfg)
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
    symbol = normalize_symbol(user_symbol)
    display_name = user_symbol.strip() if user_symbol else ""

    if not symbol:
        st.error("❌ 종목 이름 또는 티커가 비어있습니다. 다시 입력해 주세요.")
        st.stop()

    with st.spinner("데이터 불러오는 중..."):
        ov = get_us_market_overview()
        fgi = ov.get("fgi")

        df = market.get_price_data(symbol, cfg["period"])
        if df.empty:
            st.error("❌ 이 종목은 선택한 기간 동안 데이터가 부족하거나, 티커가 잘못되었습니다.")
            st.stop()

        df = analysis.add_indicators(df)
        if df.empty:
            st.error("❌ 지표 계산에 필요한 데이터가 부족합니다.")
            st.stop()

        last = df.iloc[-1]
        df_5m = market.get_intraday_5m(symbol)

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

    buy_low, buy_high, tp0, tp1, tp2, sl0, sl1 = calc_levels(df, last, cfg)

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
    state_name, action_text, recover_level, phase = compute_state_and_action(
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

    score_mkt, _, _ = compute_market_score(ov)
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
        cache_key = _ai_make_cache_key(symbol, holding_type, mode_name, avg_price, last, label_mkt, state_name, price_now)
    except Exception:
        cache_key = None

    cached = (cache_key is not None and cache_key in st.session_state.get("ai_cache", {}))
    btn_label = "🔁 AI 해석 다시 생성" if cached else "✨ AI 해석 보기"

    if cache_key is not None:
        st.button(
            btn_label,
            key=f"ai_btn_{cache_key}",
            on_click=request_ai_generation,
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
            parsed, err = ai_summarize_and_explain(
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
        ai_out = st.session_state["ai_cache"][cache_key]

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
