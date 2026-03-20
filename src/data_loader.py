"""
data_loader.py — Load and normalize raw UN Comtrade trade data.

Supports CSV and Excel formats.  Handles both "long" layout (one row per
observation with a year column) and "wide" layout (year values spread across
columns like 2000, 2001, …).
"""

import re
import pandas as pd
from pathlib import Path

from src.config import (
    RAW_FILE_CSV,
    DATA_RAW,
    COLUMN_ALIASES,
)


# ── Public API ───────────────────────────────────────────────────────────────

def find_raw_file() -> Path:
    """
    Locate the raw Comtrade data file in data/raw/.

    Priority: expected filename first, then any CSV/XLSX in the directory.
    Raises FileNotFoundError with a helpful message if nothing is found.
    """
    if RAW_FILE_CSV.exists():
        return RAW_FILE_CSV

    # Fallback: first CSV or XLSX in the raw directory
    for ext in ("*.csv", "*.xlsx", "*.xls"):
        matches = sorted(DATA_RAW.glob(ext))
        if matches:
            return matches[0]

    raise FileNotFoundError(
        f"No trade data file found in {DATA_RAW}/.\n"
        "Run the downloader first:\n"
        "  export COMTRADE_API_KEY='your-key'\n"
        "  python -m src.download_comtrade\n"
    )


def load_raw(path: Path | None = None) -> pd.DataFrame:
    """
    Load the raw WITS file and return a DataFrame with standardized columns.

    Steps:
      1. Detect file format (CSV / Excel).
      2. Read into a DataFrame.
      3. Normalize column names → snake_case via COLUMN_ALIASES.
      4. Detect wide-format year columns and melt if needed.
    """
    if path is None:
        path = find_raw_file()

    print(f"Loading raw data from: {path.name}")

    # ── Read ──────────────────────────────────────────────────────────────
    if path.suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path, engine="openpyxl")
    else:
        # Try common CSV separators
        df = _read_csv_auto(path)

    print(f"  Raw shape: {df.shape}")
    print(f"  Raw columns: {list(df.columns)}")

    # ── Normalize column names ────────────────────────────────────────────
    df = _normalize_columns(df)

    # ── Detect & handle wide format ───────────────────────────────────────
    df = _melt_if_wide(df)

    # ── Ensure year is integer ────────────────────────────────────────────
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    print(f"  Normalized shape: {df.shape}")
    print(f"  Normalized columns: {list(df.columns)}")

    return df


# ── Internal helpers ─────────────────────────────────────────────────────────

def _read_csv_auto(path: Path) -> pd.DataFrame:
    """Try comma, then semicolon, then tab as CSV separator."""
    for sep in [",", ";", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, low_memory=False)
            if len(df.columns) > 1:
                return df
        except Exception:
            continue
    # Last resort: let pandas guess
    return pd.read_csv(path, sep=None, engine="python", low_memory=False)


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename columns to canonical snake_case names using COLUMN_ALIASES.

    Any column not in the alias map is converted to snake_case as-is.
    """
    new_names = {}
    for col in df.columns:
        key = col.strip().lower().replace("_", " ").replace("-", " ")
        # Remove extra whitespace
        key = re.sub(r"\s+", " ", key).strip()
        if key in COLUMN_ALIASES:
            new_names[col] = COLUMN_ALIASES[key]
        else:
            # Generic snake_case conversion
            new_names[col] = _to_snake_case(col)

    df = df.rename(columns=new_names)

    # Handle duplicate column names after renaming by keeping first
    df = df.loc[:, ~df.columns.duplicated()]
    return df


def _to_snake_case(name: str) -> str:
    """Convert an arbitrary column name to snake_case."""
    s = name.strip()
    s = re.sub(r"[^\w\s]", "", s)       # remove special chars
    s = re.sub(r"\s+", "_", s)          # spaces → underscores
    s = re.sub(r"([a-z])([A-Z])", r"\1_\2", s)  # camelCase split
    return s.lower().strip("_")


def _melt_if_wide(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect wide-format data where year values are spread across columns
    (e.g. columns named '2000', '2001', …) and melt into long format.
    """
    year_cols = [c for c in df.columns if re.fullmatch(r"\d{4}", str(c))]

    if len(year_cols) < 3:
        # Likely already long format
        return df

    print(f"  Detected wide format: {len(year_cols)} year columns. Melting…")

    id_cols = [c for c in df.columns if c not in year_cols]
    df = df.melt(
        id_vars=id_cols,
        value_vars=year_cols,
        var_name="year",
        value_name="trade_value_usd",
    )
    return df
