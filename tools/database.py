from __future__ import annotations

import csv
import sqlite3
from typing import Any

from config import DB_PATH, _resolve_path


def create_local_database(csv_path: str = "data/sp500_companies.csv") -> None:
    csv_file = _resolve_path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(
            f"'{csv_file}' not found.\n"
            "Download from: https://www.kaggle.com/datasets/andrewmvd/sp-500-stocks"
        )

    def cap_bucket(value: Any) -> str:
        try:
            numeric = float(value)
            if numeric >= 10_000_000_000:
                return "Large"
            if numeric >= 2_000_000_000:
                return "Mid"
            return "Small"
        except Exception:
            return "Unknown"

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DROP TABLE IF EXISTS stocks")
        conn.execute(
            """
            CREATE TABLE stocks (
                ticker TEXT,
                company TEXT,
                sector TEXT,
                industry TEXT,
                market_cap TEXT,
                exchange TEXT
            )
            """
        )

        seen_tickers: set[str] = set()
        rows_to_insert: list[tuple[str, ...]] = []
        with open(csv_file, newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for raw_row in reader:
                row = {str(key).strip().lower(): value for key, value in raw_row.items()}
                ticker = (row.get("symbol") or "").strip()
                company = (row.get("shortname") or "").strip()
                if not ticker or not company or ticker in seen_tickers:
                    continue

                seen_tickers.add(ticker)
                rows_to_insert.append(
                    (
                        ticker,
                        company,
                        (row.get("sector") or "").strip(),
                        (row.get("industry") or "").strip(),
                        cap_bucket(row.get("marketcap")),
                        (row.get("exchange") or "").strip(),
                    )
                )

        conn.executemany(
            """
            INSERT INTO stocks (ticker, company, sector, industry, market_cap, exchange)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows_to_insert,
        )
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_ticker ON stocks(ticker)")
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM stocks").fetchone()[0]
        print(f"Loaded {count} companies into {DB_PATH.name}")
    finally:
        conn.close()


def query_local_db(sql: str) -> dict[str, Any]:
    if not sql.strip().lower().startswith("select"):
        return {"error": "Only SELECT queries are allowed"}

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description or []]
        return {
            "columns": columns,
            "rows": [dict(row) for row in rows],
        }
    except Exception as exc:
        return {"error": str(exc)}
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_tickers_by_sector(sector: str) -> dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(
            """
            SELECT ticker, company, sector, industry, market_cap, exchange
            FROM stocks
            WHERE lower(coalesce(sector, '')) = lower(?)
            """,
            (sector,),
        )
        rows = cursor.fetchall()
        if not rows:
            cursor = conn.execute(
                """
                SELECT ticker, company, sector, industry, market_cap, exchange
                FROM stocks
                WHERE lower(coalesce(industry, '')) LIKE lower(?)
                """,
                (f"%{sector}%",),
            )
            rows = cursor.fetchall()
    finally:
        conn.close()

    if not rows:
        return {"error": f"No stocks found for {sector}"}

    return {"sector": sector, "stocks": [dict(row) for row in rows]}
