"""
download_multi_commodity.py — Download trade data for multiple commodity categories.

Usage:
    export COMTRADE_API_KEY="your-key-here"
    python -m src.download_multi_commodity

Commodities downloaded (one HS chapter each):
    HS 10  — Cereals (wheat, corn, rice)
    HS 72  — Iron & Steel
    HS 84  — Machinery & Equipment
    HS 87  — Motor Vehicles

Rate limits (free tier): 500 calls/day, 100,000 records/call
Total calls needed: 4 chapters × 24 years × 2 flows = 192 calls
"""

import os
import sys
import time
from pathlib import Path

import pandas as pd
import comtradeapicall

# ── Configuration ────────────────────────────────────────────────────────────

COMMODITIES = {
    "cereals":   "10",   # HS 10: Cereals (wheat, corn, rice, barley)
    "steel":     "72",   # HS 72: Iron and Steel
    "machinery": "84",   # HS 84: Nuclear reactors, boilers, machinery
    "vehicles":  "87",   # HS 87: Vehicles (cars, trucks)
}

TYPE_CODE      = "C"
FREQ_CODE      = "A"
CLASSIFICATION = "HS"
FLOW_CODES     = ["M", "X"]
YEAR_START     = 2000
YEAR_END       = 2023

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def get_api_key() -> str:
    key = os.environ.get("COMTRADE_API_KEY", "").strip()
    if not key:
        print("ERROR: COMTRADE_API_KEY not set.")
        sys.exit(1)
    return key


def download_year(api_key: str, commodity_code: str, year: int, flow_code: str) -> pd.DataFrame:
    flow_label = "Imports" if flow_code == "M" else "Exports"
    print(f"    {year} {flow_label}...", end=" ", flush=True)

    try:
        df = comtradeapicall.getFinalData(
            subscription_key=api_key,
            typeCode=TYPE_CODE,
            freqCode=FREQ_CODE,
            clCode=CLASSIFICATION,
            period=str(year),
            reporterCode=None,
            cmdCode=commodity_code,
            flowCode=flow_code,
            partnerCode=None,
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
    api_key = get_api_key()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    years = list(range(YEAR_START, YEAR_END + 1))
    total_calls = len(COMMODITIES) * len(years) * len(FLOW_CODES)
    print(f"Downloading {len(COMMODITIES)} commodity categories, {YEAR_START}–{YEAR_END}")
    print(f"Total API calls: {total_calls} (limit: 500/day)\n")

    for name, code in COMMODITIES.items():
        out_file = OUTPUT_DIR / f"comtrade_{name}_trade.csv"

        # Skip if already downloaded
        if out_file.exists():
            print(f"[{name.upper()} HS {code}] Already exists ({out_file.name}), skipping.")
            continue

        print(f"[{name.upper()} HS {code}]")
        frames = []

        for year in years:
            for flow_code in FLOW_CODES:
                df = download_year(api_key, code, year, flow_code)
                if not df.empty:
                    df["commodity_category"] = name
                    frames.append(df)
                time.sleep(1.5)  # respect rate limits

        if frames:
            result = pd.concat(frames, ignore_index=True)
            result.to_csv(out_file, index=False)
            print(f"  => Saved {len(result):,} rows to {out_file.name} ({out_file.stat().st_size/1e6:.1f} MB)\n")
        else:
            print(f"  => No data downloaded for {name}\n")

    print("Done.")


if __name__ == "__main__":
    main()
