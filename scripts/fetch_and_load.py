import os
import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

API_URL = "https://www.alphavantage.co/query"


def fetch_stock_data(symbol: str):
  
    """Here we are Fetching stock data from API and returns parsed list of rows."""
  
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        raise ValueError("ALPHA_VANTAGE_API_KEY is not set")

    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": api_key
    }

    try:
        resp = requests.get(API_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        # Error handling for API call
        print(f"[ERROR] API request failed: {e}")
        raise

    time_series = data.get("Time Series (Daily)")
    if not time_series:
        print("[WARN] No 'Time Series (Daily)' in API response")
        return []

    rows = []
    for date_str, values in time_series.items():
        try:
            ts = datetime.strptime(date_str, "%Y-%m-%d")
            rows.append(
                (
                    symbol,
                    ts,
                    float(values.get("1. open", 0)),
                    float(values.get("2. high", 0)),
                    float(values.get("3. low", 0)),
                    float(values.get("4. close", 0)),
                    int(values.get("5. volume", 0)),
                )
            )
        except Exception as e:
            # Skip bad records but continue
            print(f"[WARN] Skipping bad record for {date_str}: {e}")
            continue

    return rows


def insert_into_db(rows):
    """Insert list of (symbol, ts, open, high, low, close, volume) into Postgres."""
    if not rows:
        print("[INFO] No rows to insert")
        return

    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST", "postgres"),
            port=os.getenv("POSTGRES_PORT", "5432"),
        )
        conn.autocommit = True
        cur = conn.cursor()

        query = """
        INSERT INTO stock_prices
        (symbol, ts, open, high, low, close, volume)
        VALUES %s;
        """

        execute_values(cur, query, rows)
        cur.close()
        conn.close()
        print(f"[INFO] Inserted {len(rows)} rows")

    except Exception as e:
        # Error handling for DB
        print(f"[ERROR] DB insert failed: {e}")
        raise


def main():
    symbol = os.getenv("STOCK_SYMBOL", "AAPL")
    print(f"[INFO] Fetching data for {symbol}")
    rows = fetch_stock_data(symbol)
    insert_into_db(rows)


if __name__ == "__main__":
    main()

