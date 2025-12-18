import requests
import yfinance as yf
import pandas as pd


BIGTECH_LIST = [
    ("NVDA", "NVDA"),
    ("AAPL", "AAPL"),
    ("MSFT", "MSFT"),
    ("AMZN", "AMZN"),
    ("META", "META"),
    ("GOOGL", "GOOGL"),
    ("TSLA", "TSLA"),
]

SECTOR_ETF_LIST = [
    ("기술주 (XLK)", "XLK"),
    ("반도체 (SOXX)", "SOXX"),
    ("금융 (XLF)", "XLF"),
    ("헬스케어 (XLV)", "XLV"),
    ("에너지 (XLE)", "XLE"),
    ("커뮤니케이션 (XLC)", "XLC"),
]


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


def get_us_market_overview():
    overview = {}

    nq_last, nq_chg, nq_state = safe_last_change_info("NQ=F")
    es_last, es_chg, es_state = safe_last_change_info("ES=F")
    overview["futures"] = {
        "nasdaq": {"last": nq_last, "chg_pct": nq_chg, "state": nq_state},
        "sp500": {"last": es_last, "chg_pct": es_chg, "state": es_state},
    }

    tnx_last, tnx_chg, tnx_state = safe_last_change_info("^TNX")
    if tnx_last is not None:
        us10y = tnx_last / 10.0
        us10y_chg = tnx_chg / 10.0 if tnx_chg is not None else None
    else:
        us10y, us10y_chg = None, None

    dxy_last, dxy_chg, dxy_state = safe_last_change_info("DX-Y.NYB")

    overview["rates_fx"] = {
        "us10y": us10y,
        "us10y_chg": us10y_chg,
        "us10y_state": tnx_state,
        "dxy": dxy_last,
        "dxy_chg": dxy_chg,
        "dxy_state": dxy_state,
    }

    ixic_last, ixic_chg, ixic_state = safe_last_change_info("^IXIC")
    gspc_last, gspc_chg, gspc_state = safe_last_change_info("^GSPC")
    overview["indexes"] = {
        "nasdaq": {"last": ixic_last, "chg_pct": ixic_chg, "state": ixic_state},
        "sp500": {"last": gspc_last, "chg_pct": gspc_chg, "state": gspc_state},
    }

    etfs = [
        get_etf_price_with_prepost("QQQ", "QQQ (나스닥100 ETF)"),
        get_etf_price_with_prepost("VOO", "VOO (S&P500 ETF)"),
        get_etf_price_with_prepost("SOXX", "SOXX (반도체 ETF)"),
    ]
    overview["etfs"] = etfs

    overview["fgi"] = fetch_fgi()

    bigtech = []
    score_bt = 0
    for sym, _ in BIGTECH_LIST:
        _, chg, _ = safe_last_change_info(sym)
        if chg is not None:
            if chg >= 1:
                score_bt += 1
            elif chg <= -1:
                score_bt -= 1
        bigtech.append({"symbol": sym, "chg": chg})
    overview["bigtech"] = {"score": score_bt, "items": bigtech}

    sector = []
    score_sec = 0
    for label, sym in SECTOR_ETF_LIST:
        _, chg, _ = safe_last_change_info(sym)
        if chg is not None:
            if chg >= 0.8:
                score_sec += 1
            elif chg <= -0.8:
                score_sec -= 1
        sector.append({"label": label, "symbol": sym, "chg": chg})
    overview["sector"] = {"score": score_sec, "items": sector}

    return overview


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
