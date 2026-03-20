"""
download_comtrade.py — Download energy trade data from UN Comtrade API.

Usage:
    # Set your API key as an environment variable first:
    export COMTRADE_API_KEY="your-key-here"

    # Then run:
    python -m src.download_comtrade

How to get an API key (free):
    1. Go to https://comtradedeveloper.un.org
    2. Sign up for a free account
    3. Subscribe to the "comtrade - v1" product (free tier)
    4. Copy your Primary Key from the profile page

Rate limits (free tier):
    - 500 calls/day
    - Up to 100,000 records per call
"""

import os
import sys
import time
from pathlib import Path

import pandas as pd
import comtradeapicall

# ── Configuration ────────────────────────────────────────────────────────────

# HS Chapter 27: Mineral fuels, mineral oils, and products of their distillation
COMMODITY_CODE = "27"

# Annual data, goods (commodities)
TYPE_CODE = "C"
FREQ_CODE = "A"
CLASSIFICATION = "HS"

# All reporters, all partners
REPORTER_CODE = None  # None = all
PARTNER_CODE = None   # None = all

# Import (M) and Export (X)
FLOW_CODES = ["M", "X"]

# Year range
YEAR_START = 2000
YEAR_END = 2023

# Output path
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "comtrade_energy_trade.csv"


def get_api_key() -> str:
    """Read the API key from the COMTRADE_API_KEY environment variable."""
    key = os.environ.get("COMTRADE_API_KEY", "").strip()
    if not key:
        print(
            "ERROR: COMTRADE_API_KEY environment variable not set.\n"
            "\n"
            "To get a free API key:\n"
            "  1. Go to https://comtradedeveloper.un.org\n"
            "  2. Sign up and subscribe to 'comtrade - v1' (free)\n"
            "  3. Copy your Primary Key\n"
            "  4. Run: export COMTRADE_API_KEY='your-key-here'\n"
        )
        sys.exit(1)
    return key


def download_year(api_key: str, year: int, flow_code: str) -> pd.DataFrame:
    """
    Download trade data for a single year and flow direction.

    Returns a DataFrame, or an empty DataFrame if the call fails.
    """
    flow_label = "Imports" if flow_code == "M" else "Exports"
    print(f"  Downloading {year} {flow_label}...", end=" ", flush=True)

    try:
        df = comtradeapicall.getFinalData(
            subscription_key=api_key,
            typeCode=TYPE_CODE,
            freqCode=FREQ_CODE,
            clCode=CLASSIFICATION,
            period=str(year),
            reporterCode=REPORTER_CODE,
            cmdCode=COMMODITY_CODE,
            flowCode=flow_code,
            partnerCode=PARTNER_CODE,
            partner2Code=None,
            customsCode=None,
            motCode=None,
            maxRecords=100000,
            format_output="JSON",
            aggregateBy=None,
            breakdownMode="classic",
            countOnly=None,
            includeDesc=True,
        )

        if df is not None and not df.empty:
            print(f"{len(df):,} records")
            return df
        else:
            print("0 records")
            return pd.DataFrame()

    except Exception as e:
        print(f"FAILED: {e}")
        return pd.DataFrame()


def main():
    """Download all energy trade data year-by-year and save to CSV."""
    api_key = get_api_key()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    years = list(range(YEAR_START, YEAR_END + 1))
    all_frames = []

    print(f"Downloading HS Chapter {COMMODITY_CODE} trade data ({YEAR_START}–{YEAR_END})")
    print(f"Output: {OUTPUT_FILE}\n")

    for year in years:
        for flow_code in FLOW_CODES:
            df = download_year(api_key, year, flow_code)
            if not df.empty:
                all_frames.append(df)

            # Respect rate limits: pause between calls
            time.sleep(1.5)

    if not all_frames:
        print("\nNo data was downloaded. Check your API key and network connection.")
        sys.exit(1)

    # Concatenate all years
    result = pd.concat(all_frames, ignore_index=True)
    print(f"\nTotal records: {len(result):,}")
    print(f"Columns: {list(result.columns)}")

    # Save
    result.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved to: {OUTPUT_FILE}")
    print(f"File size: {OUTPUT_FILE.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
