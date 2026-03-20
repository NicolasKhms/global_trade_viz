"""
utils.py — Country name standardization and ISO-3 code utilities.
"""

import pycountry
import pandas as pd

# ── Manual overrides for common WITS names that pycountry doesn't resolve ────
_COUNTRY_NAME_OVERRIDES = {
    "world": None,  # aggregate row, not a country
    "unspecified": None,
    "other asia, nes": None,
    "areas, nes": None,
    "special categories": None,
    "free zones": None,
    "bunkers": None,
    # Common WITS spellings → pycountry-recognized names
    "korea, rep.": "Korea, Republic of",
    "korea, dem. rep.": "Korea, Democratic People's Republic of",
    "iran, islamic rep.": "Iran, Islamic Republic of",
    "egypt, arab rep.": "Egypt",
    "venezuela, rb": "Venezuela, Bolivarian Republic of",
    "russian federation": "Russian Federation",
    "czech republic": "Czechia",
    "slovak republic": "Slovakia",
    "congo, dem. rep.": "Congo, The Democratic Republic of the",
    "congo, rep.": "Congo",
    "cote d'ivoire": "Côte d'Ivoire",
    "lao pdr": "Lao People's Democratic Republic",
    "syria": "Syrian Arab Republic",
    "vietnam": "Viet Nam",
    "brunei": "Brunei Darussalam",
    "bolivia": "Bolivia, Plurinational State of",
    "tanzania": "Tanzania, United Republic of",
    "macedonia, fyr": "North Macedonia",
    "hong kong, china": "Hong Kong",
    "macao, china": "Macao",
    "taiwan, china": "Taiwan, Province of China",
    "eu-27": None,  # aggregate
    "eu-28": None,
    "european union": None,
    "sub-saharan africa": None,
    "east asia & pacific": None,
    "middle east & north africa": None,
    "latin america & caribbean": None,
    "south asia": None,
    "europe & central asia": None,
    "north america": None,
}


def _lookup_iso3(name: str) -> str | None:
    """Return ISO-3166-1 alpha-3 code for a country name, or None."""
    if name is None:
        return None
    try:
        return pycountry.countries.lookup(name).alpha_3
    except LookupError:
        # Try fuzzy search as fallback
        try:
            results = pycountry.countries.search_fuzzy(name)
            if results:
                return results[0].alpha_3
        except LookupError:
            pass
    return None


def standardize_country(name: str) -> tuple[str | None, str | None]:
    """
    Given a raw country name from WITS, return (standardized_name, iso3_code).

    Returns (None, None) for aggregate/invalid entries (e.g. "World", "EU-27").
    """
    if pd.isna(name) or not isinstance(name, str):
        return None, None

    key = name.strip().lower()

    # Check overrides first
    if key in _COUNTRY_NAME_OVERRIDES:
        override = _COUNTRY_NAME_OVERRIDES[key]
        if override is None:
            return None, None  # intentionally excluded aggregate
        iso3 = _lookup_iso3(override)
        return override, iso3

    # Direct lookup
    iso3 = _lookup_iso3(name.strip())
    if iso3:
        country_obj = pycountry.countries.get(alpha_3=iso3)
        return country_obj.name if country_obj else name.strip(), iso3

    return name.strip(), None  # keep original name, flag missing ISO


def add_iso3_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add `reporter_iso3` and `partner_iso3` columns based on name standardization.

    Also cleans reporter/partner names. Rows where the reporter resolves to None
    (aggregates like "World") are kept but flagged with iso3 = NaN.
    """
    df = df.copy()

    if "reporter" in df.columns:
        resolved = df["reporter"].apply(standardize_country)
        df["reporter_std"] = resolved.apply(lambda x: x[0])
        df["reporter_iso3"] = resolved.apply(lambda x: x[1])

    if "partner" in df.columns:
        resolved = df["partner"].apply(standardize_country)
        df["partner_std"] = resolved.apply(lambda x: x[0])
        df["partner_iso3"] = resolved.apply(lambda x: x[1])

    return df


def report_country_matching(df: pd.DataFrame, col: str = "reporter") -> pd.DataFrame:
    """
    Return a summary of country-matching quality for a given column.
    Useful for documenting matching issues.
    """
    iso_col = f"{col}_iso3"
    if iso_col not in df.columns:
        raise ValueError(f"Column {iso_col} not found. Run add_iso3_columns first.")

    total = df[col].nunique()
    matched = df.loc[df[iso_col].notna(), col].nunique()
    unmatched_names = sorted(
        df.loc[df[iso_col].isna(), col].dropna().unique().tolist()
    )

    summary = pd.DataFrame(
        {
            "metric": ["total_unique", "matched", "unmatched", "match_rate"],
            "value": [
                total,
                matched,
                total - matched,
                f"{matched / total:.1%}" if total > 0 else "N/A",
            ],
        }
    )

    return summary, unmatched_names
