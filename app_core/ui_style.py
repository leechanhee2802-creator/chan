import streamlit as st

def inject_css():
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
