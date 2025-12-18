import streamlit as st

def init_session_state():
    defaults = {
        "recent_symbols": [],
        "favorite_symbols": [],
        "selected_symbol": "엔비디아",
        "run_from_side": False,
        "symbol_input": "엔비디아",
        "pending_symbol": "",
        "scroll_to_result": False,
        "scan_results": None,
        "show_result": False,
        "analysis_params": None,
        "ai_cache": {},
        "ai_request": False,
        "ai_request_key": None,
        "ai_model_name": "gpt-4o-mini",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
