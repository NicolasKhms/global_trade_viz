"""
config.py — Project-wide paths, constants, and energy product mappings.
"""

from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"
TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"

# Raw file produced by src/download_comtrade.py
RAW_FILE_CSV = DATA_RAW / "comtrade_energy_trade.csv"

# ── Processed file names ─────────────────────────────────────────────────────
PROCESSED_ENERGY_TRADE = DATA_PROCESSED / "energy_trade.csv"
PROCESSED_COUNTRY_SUMMARY = DATA_PROCESSED / "country_summary.csv"
PROCESSED_PARTNER_SUMMARY = DATA_PROCESSED / "partner_summary.csv"

# ── Year range ───────────────────────────────────────────────────────────────
YEAR_MIN = 2000
YEAR_MAX = 2023

# ── Energy product filtering ─────────────────────────────────────────────────
# HS Chapter 27: Mineral fuels, mineral oils, and products of their distillation
# We match on both HS codes (if available) and product-name keywords.

ENERGY_HS_CHAPTERS = ["27"]  # two-digit HS chapter

ENERGY_HS_CODES_4DIGIT = [
    "2701",  # Coal; briquettes, ovoids, and similar solid fuels from coal
    "2702",  # Lignite
    "2704",  # Coke and semi-coke of coal, lignite, or peat
    "2709",  # Petroleum oils, crude
    "2710",  # Petroleum oils, not crude
    "2711",  # Petroleum gases and other gaseous hydrocarbons (LNG, LPG)
    "2713",  # Petroleum coke, petroleum bitumen
    "2716",  # Electrical energy
]

# Keywords to match in product name/description columns (case-insensitive)
ENERGY_KEYWORDS = [
    "mineral fuel",
    "petroleum",
    "crude oil",
    "natural gas",
    "coal",
    "lignite",
    "coke",
    "fuel oil",
    "gasoline",
    "diesel",
    "kerosene",
    "liquefied",
    "bituminous",
    "electrical energy",
    "lng",
    "lpg",
]

# ── Column name mapping ──────────────────────────────────────────────────────
# Maps common WITS column names (case-insensitive) to our canonical names.
# The loader will try to match raw columns against these.

COLUMN_ALIASES = {
    # reporter
    "reporter": "reporter",
    "reportername": "reporter",
    "reporter name": "reporter",
    "reporting economy": "reporter",
    "reporteriso3": "reporter_iso3",
    "reporter iso3": "reporter_iso3",
    # partner
    "partner": "partner",
    "partnername": "partner",
    "partner name": "partner",
    "partneriso3": "partner_iso3",
    "partner iso3": "partner_iso3",
    # product
    "productcode": "product_code",
    "product code": "product_code",
    "product": "product",
    "productdescription": "product",
    "product description": "product",
    "productgroup": "product",
    "product group": "product",
    "nomenclature": "nomenclature",
    # trade flow
    "tradeflowcode": "flow_code",
    "tradeflowname": "flow",
    "trade flow": "flow",
    "indicator": "flow",
    "indicatortype": "flow",
    "indicator type": "flow",
    # year / value
    "year": "year",
    "period": "year",
    "refyear": "year",
    "tradevalue": "trade_value_usd",
    "trade value": "trade_value_usd",
    "tradevaluein1000usd": "trade_value_1000usd",
    "trade value in 1000 usd": "trade_value_1000usd",
    "value": "trade_value_usd",
    "primaryvalue": "trade_value_usd",
    # UN Comtrade API-specific columns
    "reporterdesc": "reporter",
    "reportercode": "reporter_code",
    "reporteriso": "reporter_iso3",
    "partnerdesc": "partner",
    "partnercode": "partner_code",
    "partneriso": "partner_iso3",
    "cmddesc": "product",
    "cmdcode": "product_code",
    "flowdesc": "flow",
    "flowcode": "flow_code",
    "cifvalue": "cif_value",
    "fobvalue": "fob_value",
}

# ── Flow labels ──────────────────────────────────────────────────────────────
IMPORT_LABELS = ["import", "imports", "gross imp.", "gross imports"]
EXPORT_LABELS = ["export", "exports", "gross exp.", "gross exports"]
