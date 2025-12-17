"""Session state helpers."""

import streamlit as st


def initialize_session_state():
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

    if "show_result" not in st.session_state:
        st.session_state["show_result"] = False
    if "analysis_params" not in st.session_state:
        st.session_state["analysis_params"] = None

    if "ai_cache" not in st.session_state:
        st.session_state["ai_cache"] = {}
    if "ai_request" not in st.session_state:
        st.session_state["ai_request"] = False
    if "ai_request_key" not in st.session_state:
        st.session_state["ai_request_key"] = None

    if "refresh_key" not in st.session_state:
        st.session_state["refresh_key"] = 0

    if st.session_state.get("pending_symbol"):
        ps = st.session_state["pending_symbol"]
        st.session_state["symbol_input"] = ps
        st.session_state["selected_symbol"] = ps
        st.session_state["run_from_side"] = True
        st.session_state["pending_symbol"] = ""
