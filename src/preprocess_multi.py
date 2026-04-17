"""
preprocess_multi.py — Process multi-commodity raw CSVs into dashboard-ready files.

Run this after downloading new commodity data:
    python -m src.preprocess_multi

Outputs per commodity in data/processed/:
    {category}_country_summary.csv  — reporter × year (imports, exports, balance)
    {category}_partner_flow.csv     — reporter × partner × year × flow (bilateral)

For energy, derives from existing energy_trade.csv (no re-download needed).
For others, reads data/raw/comtrade_{category}_trade.csv.
"""

import sys
from pathlib import Path

import pandas as pd

from src.config import (
    DATA_RAW,
    DATA_PROCESSED,
    IMPORT_LABELS,
    EXPORT_LABELS,
    COLUMN_ALIASES,
    YEAR_MIN,
    YEAR_MAX,
)
from src.utils import add_iso3_columns

import re

# ── Commodity definitions ─────────────────────────────────────────────────────

COMMODITY_SOURCES = {
    "energy":    DATA_PROCESSED / "energy_trade.csv",         # already processed
    "cereals":   DATA_RAW / "comtrade_cereals_trade.csv",
    "steel":     DATA_RAW / "comtrade_steel_trade.csv",
    "machinery": DATA_RAW / "comtrade_machinery_trade.csv",
    "vehicles":  DATA_RAW / "comtrade_vehicles_trade.csv",
}

AGGREGATE_PARTNERS = {
    "World", "Areas, nes", "Special Categories", "Free Zones",
    "Bunkers", "Other Asia, nes", "Unspecified",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename raw columns to canonical names using COLUMN_ALIASES."""
    new_names = {}
    for col in df.columns:
        key = re.sub(r"\s+", " ", col.strip().lower().replace("_", " ").replace("-", " "))
        new_names[col] = COLUMN_ALIASES.get(key, col.lower().replace(" ", "_"))
    df = df.rename(columns=new_names)
    return df.loc[:, ~df.columns.duplicated()]


def _normalize_flow(val) -> str | None:
    if pd.isna(val):
        return None
    s = str(val).strip().lower()
    if s in IMPORT_LABELS:
        return "Import"
    if s in EXPORT_LABELS:
        return "Export"
    return str(val).strip()


def clean_raw(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize columns, clean values, filter year range."""
    df = _normalize_columns(df)

    # Unify trade value
    if "trade_value_1000usd" in df.columns and "trade_value_usd" not in df.columns:
        df["trade_value_usd"] = pd.to_numeric(df["trade_value_1000usd"], errors="coerce") * 1000
        df = df.drop(columns=["trade_value_1000usd"])
    elif "trade_value_usd" in df.columns:
        df["trade_value_usd"] = pd.to_numeric(df["trade_value_usd"], errors="coerce")

    # Drop missing
    required = [c for c in ["reporter", "year", "trade_value_usd"] if c in df.columns]
    df = df.dropna(subset=required)
    df = df[df["trade_value_usd"] > 0]

    # Year range
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        df = df[(df["year"] >= YEAR_MIN) & (df["year"] <= YEAR_MAX)]

    # Normalize flow
    if "flow" in df.columns:
        df["flow"] = df["flow"].apply(_normalize_flow)

    # Drop aggregate partners
    if "partner" in df.columns:
        df = df[~df["partner"].isin(AGGREGATE_PARTNERS)]

    return df


def build_country_summary(df: pd.DataFrame) -> pd.DataFrame:
    """reporter × year → total_imports, total_exports, trade_balance."""
    iso_col = "reporter_iso3" if "reporter_iso3" in df.columns else None
    group_cols = ["reporter"] + ([iso_col] if iso_col else []) + ["year"]

    imp = (
        df[df["flow"] == "Import"]
        .groupby(group_cols, dropna=False)["trade_value_usd"]
        .sum().reset_index().rename(columns={"trade_value_usd": "total_imports"})
    )
    exp = (
        df[df["flow"] == "Export"]
        .groupby(group_cols, dropna=False)["trade_value_usd"]
        .sum().reset_index().rename(columns={"trade_value_usd": "total_exports"})
    )
    summary = pd.merge(imp, exp, on=group_cols, how="outer")
    summary = summary.fillna({"total_imports": 0, "total_exports": 0})
    summary["trade_balance"] = summary["total_exports"] - summary["total_imports"]
    summary["total_trade"] = summary["total_imports"] + summary["total_exports"]
    return summary


def build_partner_flow(df: pd.DataFrame) -> pd.DataFrame:
    """reporter × partner × year × flow → trade_value_usd (bilateral detail)."""
    group_cols = [c for c in
                  ["reporter", "reporter_iso3", "partner", "partner_iso3", "year", "flow"]
                  if c in df.columns]
    return (
        df.groupby(group_cols, dropna=False)["trade_value_usd"]
        .sum().reset_index()
    )


def process_category(category: str, source_path: Path) -> bool:
    """Process one commodity category and save output files. Returns True on success."""
    out_cs = DATA_PROCESSED / f"{category}_country_summary.csv"
    out_pf = DATA_PROCESSED / f"{category}_partner_flow.csv"

    if out_cs.exists() and out_pf.exists():
        print(f"  [{category}] Already processed, skipping.")
        return True

    if not source_path.exists():
        print(f"  [{category}] Raw file not found: {source_path.name} — skipping.")
        return False

    print(f"  [{category}] Loading {source_path.name} ...", end=" ", flush=True)
    df = pd.read_csv(source_path, low_memory=False)
    print(f"{len(df):,} rows")

    # Energy source is already cleaned; others need full cleaning + ISO3
    if category == "energy":
        # energy_trade.csv already has canonical columns and ISO3 codes
        if "partner" in df.columns:
            df = df[~df["partner"].isin(AGGREGATE_PARTNERS)]
        if "year" in df.columns:
            df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    else:
        df = clean_raw(df)
        print(f"    After cleaning: {len(df):,} rows")
        print(f"    Adding ISO-3 codes...")
        df = add_iso3_columns(df)

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    cs = build_country_summary(df)
    cs.to_csv(out_cs, index=False)
    print(f"    Saved country_summary: {len(cs):,} rows → {out_cs.name}")

    pf = build_partner_flow(df)
    pf.to_csv(out_pf, index=False)
    print(f"    Saved partner_flow:    {len(pf):,} rows → {out_pf.name}")

    return True


def main():
    print("=== Multi-Commodity Preprocessing ===\n")
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    results = {}
    for category, source in COMMODITY_SOURCES.items():
        results[category] = process_category(category, source)

    print("\n=== Summary ===")
    for cat, ok in results.items():
        status = "✓" if ok else "✗ (raw file missing)"
        print(f"  {cat:12s} {status}")


if __name__ == "__main__":
    main()
