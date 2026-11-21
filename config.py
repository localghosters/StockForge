from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "database" / "stockforge.db"

TICKERS = ["AAPL", "MSFT", "RELIANCE.NS"]
START_DATE = "2018-01-01"
END_DATE = None

SHORT_WINDOW = 20
LONG_WINDOW = 50

INITIAL_CAPITAL = 100000
FEE_RATE = 0.001
