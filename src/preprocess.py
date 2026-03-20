"""
preprocess.py — Filter, clean, and reshape trade data for visualization.

Main outputs:
  1. energy_trade.csv       — cleaned row-level energy trade data
  2. country_summary.csv    — country × year aggregation (imports, exports, balance)
  3. partner_summary.csv    — reporter × partner × year aggregation
"""

import pandas as pd
import numpy as np

from src.config import (
    ENERGY_HS_CHAPTERS,
    ENERGY_HS_CODES_4DIGIT,
    ENERGY_KEYWORDS,
    YEAR_MIN,
    YEAR_MAX,
    IMPORT_LABELS,
    EXPORT_LABELS,
    PROCESSED_ENERGY_TRADE,
    PROCESSED_COUNTRY_SUMMARY,
    PROCESSED_PARTNER_SUMMARY,
)
from src.utils import add_iso3_columns


# ── Energy filtering ─────────────────────────────────────────────────────────

def is_energy_by_code(code: str) -> bool:
    """Check if a product code (HS) belongs to an energy category."""
    if pd.isna(code):
        return False
    code = str(code).strip()
    # Chapter-level match (first 2 digits)
    if code[:2] in ENERGY_HS_CHAPTERS:
        return True
    # 4-digit match
    if code[:4] in ENERGY_HS_CODES_4DIGIT:
        return True
    return False


def is_energy_by_name(name: str) -> bool:
    """Check if a product name/description contains energy-related keywords."""
    if pd.isna(name):
        return False
    lower = str(name).lower()
    return any(kw in lower for kw in ENERGY_KEYWORDS)


def filter_energy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return rows matching energy products by code and/or by name.

    Uses an OR strategy: a row is kept if either the product code or the
    product name matches energy criteria.
    """
    has_code = "product_code" in df.columns
    has_name = "product" in df.columns

    if not has_code and not has_name:
        print("WARNING: No product_code or product column found. "
              "Returning full dataset (no energy filter applied).")
        return df

    mask = pd.Series(False, index=df.index)

    if has_code:
        mask |= df["product_code"].apply(is_energy_by_code)

    if has_name:
        mask |= df["product"].apply(is_energy_by_name)

    filtered = df[mask].copy()
    print(f"  Energy filter: {len(filtered):,} / {len(df):,} rows retained "
          f"({len(filtered) / len(df):.1%})")
    return filtered


# ── Cleaning ─────────────────────────────────────────────────────────────────

def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply standard cleaning steps:
      - Convert trade_value columns to numeric
      - Handle "trade_value_1000usd" → multiply by 1000
      - Drop rows with missing reporter, year, or trade value
      - Filter to valid year range
      - Normalize flow labels to 'Import' / 'Export'
    """
    df = df.copy()

    # ── Unify trade value column ──────────────────────────────────────────
    if "trade_value_1000usd" in df.columns and "trade_value_usd" not in df.columns:
        df["trade_value_usd"] = (
            pd.to_numeric(df["trade_value_1000usd"], errors="coerce") * 1000
        )
        df = df.drop(columns=["trade_value_1000usd"])
    elif "trade_value_usd" in df.columns:
        df["trade_value_usd"] = pd.to_numeric(
            df["trade_value_usd"], errors="coerce"
        )

    # ── Drop rows missing critical fields ─────────────────────────────────
    required = ["reporter", "year", "trade_value_usd"]
    existing_required = [c for c in required if c in df.columns]
    before = len(df)
    df = df.dropna(subset=existing_required)
    print(f"  Dropped {before - len(df):,} rows with missing required fields.")

    # ── Remove zero / negative trade values ───────────────────────────────
    if "trade_value_usd" in df.columns:
        df = df[df["trade_value_usd"] > 0]

    # ── Filter year range ─────────────────────────────────────────────────
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        df = df[(df["year"] >= YEAR_MIN) & (df["year"] <= YEAR_MAX)]

    # ── Normalize flow labels ─────────────────────────────────────────────
    if "flow" in df.columns:
        df["flow"] = df["flow"].apply(_normalize_flow)

    print(f"  Clean shape: {df.shape}")
    return df


def _normalize_flow(val) -> str | None:
    """Map various flow labels to 'Import' or 'Export'."""
    if pd.isna(val):
        return None
    s = str(val).strip().lower()
    if s in IMPORT_LABELS:
        return "Import"
    if s in EXPORT_LABELS:
        return "Export"
    return str(val).strip()  # keep original if unknown


# ── Summary datasets ─────────────────────────────────────────────────────────

def build_country_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate to country × year level with total imports, exports, and balance.

    Requires a 'flow' column with values 'Import' / 'Export'.
    If flow is missing, aggregates total trade value only.
    """
    if "flow" not in df.columns:
        agg = (
            df.groupby(["reporter", "year"], dropna=False)["trade_value_usd"]
            .sum()
            .reset_index()
            .rename(columns={"reporter": "country", "trade_value_usd": "total_trade"})
        )
        return agg

    imports = (
        df[df["flow"] == "Import"]
        .groupby(["reporter", "year"], dropna=False)["trade_value_usd"]
        .sum()
        .reset_index()
        .rename(columns={"trade_value_usd": "total_imports"})
    )

    exports = (
        df[df["flow"] == "Export"]
        .groupby(["reporter", "year"], dropna=False)["trade_value_usd"]
        .sum()
        .reset_index()
        .rename(columns={"trade_value_usd": "total_exports"})
    )

    summary = pd.merge(imports, exports, on=["reporter", "year"], how="outer")
    summary = summary.fillna({"total_imports": 0, "total_exports": 0})
    summary["trade_balance"] = summary["total_exports"] - summary["total_imports"]
    summary = summary.rename(columns={"reporter": "country"})

    return summary


def build_partner_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate to reporter × partner × year level."""
    group_cols = ["reporter", "partner", "year"]
    existing = [c for c in group_cols if c in df.columns]

    agg = (
        df.groupby(existing, dropna=False)["trade_value_usd"]
        .sum()
        .reset_index()
        .rename(columns={"trade_value_usd": "total_trade_value"})
    )
    return agg


# ── Pipeline entry point ─────────────────────────────────────────────────────

def run_pipeline(df_raw: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Full preprocessing pipeline: filter → clean → enrich → aggregate.

    Returns a dict with keys: 'energy_trade', 'country_summary', 'partner_summary'.
    """
    print("\n=== Preprocessing Pipeline ===")

    # 1. Filter to energy products
    df = filter_energy(df_raw)

    # 2. Clean
    df = clean(df)

    # 3. Add ISO-3 country codes
    print("  Adding ISO-3 country codes…")
    df = add_iso3_columns(df)

    # 4. Build summaries
    print("  Building country summary…")
    country_summary = build_country_summary(df)

    print("  Building partner summary…")
    partner_summary = build_partner_summary(df)

    # 5. Save
    PROCESSED_ENERGY_TRADE.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(PROCESSED_ENERGY_TRADE, index=False)
    print(f"  Saved → {PROCESSED_ENERGY_TRADE.name}  ({len(df):,} rows)")

    country_summary.to_csv(PROCESSED_COUNTRY_SUMMARY, index=False)
    print(f"  Saved → {PROCESSED_COUNTRY_SUMMARY.name}  ({len(country_summary):,} rows)")

    partner_summary.to_csv(PROCESSED_PARTNER_SUMMARY, index=False)
    print(f"  Saved → {PROCESSED_PARTNER_SUMMARY.name}  ({len(partner_summary):,} rows)")

    return {
        "energy_trade": df,
        "country_summary": country_summary,
        "partner_summary": partner_summary,
    }
