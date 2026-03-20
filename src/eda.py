"""
eda.py — Exploratory data analysis helpers.

Each function returns a DataFrame or a matplotlib/plotly figure that can be
displayed in a notebook and optionally saved.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px

from src.config import FIGURES_DIR


# ── Ensure output dir exists ─────────────────────────────────────────────────
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def data_overview(df: pd.DataFrame, label: str = "dataset") -> pd.DataFrame:
    """Print and return basic shape / missing-value stats."""
    n_rows, n_cols = df.shape
    missing = df.isnull().sum()
    missing_pct = (missing / n_rows * 100).round(1)

    info = pd.DataFrame({"missing_count": missing, "missing_pct": missing_pct})
    info = info.sort_values("missing_pct", ascending=False)

    print(f"\n── {label} overview ──")
    print(f"  Rows: {n_rows:,}   Columns: {n_cols}")
    for col in ["reporter", "partner", "year", "product", "product_code"]:
        if col in df.columns:
            print(f"  Unique {col}: {df[col].nunique():,}")
    return info


def top_reporters(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    """Top reporters by total trade value."""
    return (
        df.groupby("reporter")["trade_value_usd"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
        .reset_index()
        .rename(columns={"trade_value_usd": "total_trade_value_usd"})
    )


def top_partners(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    """Top partners by total trade value."""
    if "partner" not in df.columns:
        return pd.DataFrame()
    return (
        df.groupby("partner")["trade_value_usd"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
        .reset_index()
        .rename(columns={"trade_value_usd": "total_trade_value_usd"})
    )


def top_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top energy product categories by trade value."""
    col = "product" if "product" in df.columns else "product_code"
    if col not in df.columns:
        return pd.DataFrame()
    return (
        df.groupby(col)["trade_value_usd"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
        .reset_index()
        .rename(columns={"trade_value_usd": "total_trade_value_usd"})
    )


def yearly_total(df: pd.DataFrame) -> pd.DataFrame:
    """Total trade value by year (and flow if available)."""
    group = ["year"]
    if "flow" in df.columns:
        group.append("flow")
    return (
        df.groupby(group)["trade_value_usd"]
        .sum()
        .reset_index()
        .sort_values("year")
    )


# ── Plotting ─────────────────────────────────────────────────────────────────

def plot_top_reporters(df: pd.DataFrame, n: int = 15, save: bool = True):
    """Horizontal bar chart of top reporters."""
    data = top_reporters(df, n).sort_values("total_trade_value_usd")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(data["reporter"], data["total_trade_value_usd"] / 1e9, color="#2563eb")
    ax.set_xlabel("Total Energy Trade Value (billion USD)")
    ax.set_title(f"Top {n} Reporters by Energy Trade Value")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    if save:
        fig.savefig(FIGURES_DIR / "top_reporters.png", dpi=150, bbox_inches="tight")
    return fig


def plot_top_partners(df: pd.DataFrame, n: int = 15, save: bool = True):
    """Horizontal bar chart of top partners."""
    data = top_partners(df, n).sort_values("total_trade_value_usd")
    if data.empty:
        return None
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(data["partner"], data["total_trade_value_usd"] / 1e9, color="#059669")
    ax.set_xlabel("Total Energy Trade Value (billion USD)")
    ax.set_title(f"Top {n} Partners by Energy Trade Value")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    if save:
        fig.savefig(FIGURES_DIR / "top_partners.png", dpi=150, bbox_inches="tight")
    return fig


def plot_top_products(df: pd.DataFrame, n: int = 10, save: bool = True):
    """Horizontal bar chart of top energy product categories."""
    data = top_products(df, n).sort_values("total_trade_value_usd")
    if data.empty:
        return None
    col = "product" if "product" in data.columns else "product_code"
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(data[col], data["total_trade_value_usd"] / 1e9, color="#d97706")
    ax.set_xlabel("Total Trade Value (billion USD)")
    ax.set_title(f"Top {n} Energy Product Categories")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    if save:
        fig.savefig(FIGURES_DIR / "top_products.png", dpi=150, bbox_inches="tight")
    return fig


def plot_yearly_trend(df: pd.DataFrame, save: bool = True):
    """Line chart of total energy trade value over time."""
    data = yearly_total(df)

    fig, ax = plt.subplots(figsize=(12, 5))

    if "flow" in data.columns:
        for flow, grp in data.groupby("flow"):
            ax.plot(grp["year"], grp["trade_value_usd"] / 1e9, marker="o",
                    markersize=4, label=flow)
        ax.legend()
    else:
        ax.plot(data["year"], data["trade_value_usd"] / 1e9, marker="o",
                markersize=4, color="#2563eb")

    ax.set_xlabel("Year")
    ax.set_ylabel("Trade Value (billion USD)")
    ax.set_title("Global Energy Trade Value Over Time")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    if save:
        fig.savefig(FIGURES_DIR / "yearly_trend.png", dpi=150, bbox_inches="tight")
    return fig


def plot_choropleth(country_summary: pd.DataFrame, year: int | None = None,
                    value_col: str = "total_trade", save: bool = True):
    """
    Plotly choropleth of trade value by country for a given year.
    Falls back to sum across all years if year is None.
    """
    df = country_summary.copy()

    # Determine the value column
    if value_col not in df.columns:
        # Try alternatives
        for alt in ["total_imports", "total_exports", "total_trade"]:
            if alt in df.columns:
                value_col = alt
                break

    if year is not None:
        df = df[df["year"] == year]
        title = f"Energy Trade by Country ({year})"
    else:
        df = df.groupby("country")[value_col].sum().reset_index()
        title = "Energy Trade by Country (All Years)"

    # Need ISO codes for choropleth
    from src.utils import standardize_country
    if "country_iso3" not in df.columns:
        resolved = df["country"].apply(standardize_country)
        df["country_iso3"] = resolved.apply(lambda x: x[1])

    df = df.dropna(subset=["country_iso3"])

    fig = px.choropleth(
        df,
        locations="country_iso3",
        color=value_col,
        hover_name="country",
        color_continuous_scale="Viridis",
        title=title,
        labels={value_col: "Trade Value (USD)"},
    )
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))

    if save:
        fig.write_image(FIGURES_DIR / "choropleth.png", scale=2, width=1200, height=600)

    return fig


def trade_concentration(df: pd.DataFrame, col: str = "reporter",
                        top_n: int = 10) -> pd.DataFrame:
    """
    Compute what share of total trade the top-N entities account for.
    Useful for discussing data concentration / skewness.
    """
    totals = df.groupby(col)["trade_value_usd"].sum().sort_values(ascending=False)
    grand_total = totals.sum()

    top = totals.head(top_n)
    result = pd.DataFrame({
        col: top.index,
        "trade_value_usd": top.values,
        "share": (top.values / grand_total * 100).round(1),
        "cumulative_share": (top.values.cumsum() / grand_total * 100).round(1),
    })

    return result
