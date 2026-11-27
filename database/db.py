import sqlite3
import pandas as pd
from config import DB_PATH


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def create_tables():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                ticker TEXT NOT NULL,
                date   TEXT NOT NULL,
                open   REAL,
                high   REAL,
                low    REAL,
                close  REAL,
                volume INTEGER,
                PRIMARY KEY (ticker, date)
            )
        """)


def save_prices(ticker, df):
    rows = [
        (ticker, row.Index.strftime("%Y-%m-%d"),
         row.open, row.high, row.low, row.close, int(row.volume))
        for row in df.itertuples()
    ]
    with get_connection() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO prices VALUES (?, ?, ?, ?, ?, ?, ?)",
            rows,
        )


def load_prices(ticker, start=None):
    query = """
        SELECT date, open, high, low, close, volume
        FROM prices
        WHERE ticker = ?
    """
    params = [ticker]
    if start:
        query += " AND date >= ?"
        params.append(start)
    query += " ORDER BY date"
    with get_connection() as conn:
        return pd.read_sql_query(
            query, conn, params=params,
            parse_dates=["date"], index_col="date",
        )
