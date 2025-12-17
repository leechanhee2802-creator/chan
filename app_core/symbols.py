"""Symbol mappings and helper utilities."""

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


def normalize_symbol(user_input: str) -> str:
    name = (user_input or "").strip()
    if name in KOREAN_TICKER_MAP:
        return KOREAN_TICKER_MAP[name]
    return name.replace(" ", "").upper()
