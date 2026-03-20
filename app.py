"""
Energy Trade Explorer — MVP Dashboard

Run with:  python app.py
Then open: http://127.0.0.1:8050
"""

import sys
from pathlib import Path

import dash
from dash import dcc, html, Input, Output, State, callback, no_update
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ── Load data ────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / "data" / "processed"

df_energy = pd.read_csv(DATA_DIR / "energy_trade.csv", low_memory=False)
df_country = pd.read_csv(DATA_DIR / "country_summary.csv")
df_partner = pd.read_csv(DATA_DIR / "partner_summary.csv")

# Filter out aggregate partners like "World"
AGGREGATE_PARTNERS = {"World", "Areas, nes", "Special Categories", "Free Zones",
                       "Bunkers", "Other Asia, nes", "Unspecified"}
df_bilateral = df_energy[~df_energy["partner"].isin(AGGREGATE_PARTNERS)].copy()

YEARS = sorted(df_energy["year"].dropna().unique().astype(int))
MIN_YEAR, MAX_YEAR = YEARS[0], YEARS[-1]

# Pre-compute: total trade per country per year (imports + exports)
country_year_total = (
    df_energy[df_energy["reporter_iso3"].notna()]
    .groupby(["reporter", "reporter_iso3", "year"])["trade_value_usd"]
    .sum()
    .reset_index()
)

# ── App layout ───────────────────────────────────────────────────────────────

app = dash.Dash(__name__)
app.title = "Energy Trade Explorer"

app.layout = html.Div(
    style={"fontFamily": "system-ui, -apple-system, sans-serif", "margin": "0",
           "backgroundColor": "#0f172a", "color": "#e2e8f0", "minHeight": "100vh"},
    children=[
        # Header
        html.Div(
            style={"padding": "20px 32px", "borderBottom": "1px solid #1e293b"},
            children=[
                html.H1("🌍 Global Energy Trade Explorer",
                         style={"margin": "0", "fontSize": "24px", "fontWeight": "600"}),
                html.P("Mineral fuels trade flows between countries (UN Comtrade, HS Chapter 27)",
                        style={"margin": "4px 0 0", "color": "#94a3b8", "fontSize": "14px"}),
            ],
        ),
        # Year slider
        html.Div(
            style={"padding": "16px 32px", "backgroundColor": "#1e293b"},
            children=[
                html.Label("Year", style={"fontWeight": "500", "fontSize": "14px"}),
                dcc.Slider(
                    id="year-slider",
                    min=MIN_YEAR, max=MAX_YEAR, step=1,
                    value=MAX_YEAR,
                    marks={y: str(y) for y in range(MIN_YEAR, MAX_YEAR + 1, 4)},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ],
        ),
        # Main content: map + side panel
        html.Div(
            style={"display": "flex", "flexWrap": "wrap", "gap": "0"},
            children=[
                # Map
                html.Div(
                    style={"flex": "2", "minWidth": "500px"},
                    children=[
                        dcc.Graph(id="choropleth", style={"height": "520px"},
                                  config={"displayModeBar": False}),
                    ],
                ),
                # Side panel
                html.Div(
                    id="side-panel",
                    style={"flex": "1", "minWidth": "360px", "padding": "16px 24px",
                           "backgroundColor": "#1e293b", "overflowY": "auto",
                           "maxHeight": "520px"},
                    children=[
                        html.Div(id="country-info", children=[
                            html.P("Click a country on the map to explore its energy trade dependencies.",
                                   style={"color": "#94a3b8", "fontSize": "14px",
                                          "marginTop": "40px", "textAlign": "center"}),
                        ]),
                    ],
                ),
            ],
        ),
        # Bottom: import/export toggle
        html.Div(
            style={"padding": "12px 32px", "display": "flex", "gap": "16px",
                    "alignItems": "center", "borderTop": "1px solid #1e293b"},
            children=[
                html.Label("Map shows:", style={"fontSize": "14px", "color": "#94a3b8"}),
                dcc.RadioItems(
                    id="flow-toggle",
                    options=[
                        {"label": " Total trade", "value": "total"},
                        {"label": " Imports only", "value": "Import"},
                        {"label": " Exports only", "value": "Export"},
                    ],
                    value="total",
                    inline=True,
                    style={"fontSize": "14px"},
                    labelStyle={"marginRight": "20px", "cursor": "pointer"},
                ),
            ],
        ),
    ],
)


# ── Callbacks ────────────────────────────────────────────────────────────────

@callback(
    Output("choropleth", "figure"),
    Input("year-slider", "value"),
    Input("flow-toggle", "value"),
)
def update_map(year, flow):
    """Redraw the choropleth for the selected year and flow."""
    if flow == "total":
        data = country_year_total[country_year_total["year"] == year]
    else:
        data = (
            df_energy[
                (df_energy["year"] == year)
                & (df_energy["flow"] == flow)
                & df_energy["reporter_iso3"].notna()
            ]
            .groupby(["reporter", "reporter_iso3"])["trade_value_usd"]
            .sum()
            .reset_index()
        )

    if len(data) > 0:
        q95 = data["trade_value_usd"].quantile(0.95)
        if pd.isna(q95) or q95 <= 0:
            q95 = data["trade_value_usd"].max()
        color_max = float(q95) if (pd.notna(q95) and q95 > 0) else 1.0
    else:
        color_max = 1.0

    fig = px.choropleth(
        data,
        locations="reporter_iso3",
        color="trade_value_usd",
        hover_name="reporter",
        color_continuous_scale="YlOrRd",
        range_color=[0, color_max],
        labels={"trade_value_usd": "Trade Value (USD)"},
    )

    fig.update_layout(
        geo=dict(
            showframe=False, showcoastlines=True,
            coastlinecolor="#334155",
            landcolor="#1e293b", oceancolor="#0f172a",
            projection_type="natural earth",
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_colorbar=dict(
        title=dict(text="USD", font=dict(color="#94a3b8")),
        tickfont=dict(color="#94a3b8"),
        bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=0, r=0, t=10, b=10),
        font=dict(color="#e2e8f0"),
    )

    return fig


@callback(
    Output("country-info", "children"),
    Input("choropleth", "clickData"),
    State("year-slider", "value"),
)
def update_side_panel(click_data, year):
    """When a country is clicked, show its trade dependencies."""
    if click_data is None:
        return html.P(
            "Click a country on the map to explore its energy trade dependencies.",
            style={"color": "#94a3b8", "fontSize": "14px",
                   "marginTop": "40px", "textAlign": "center"},
        )

    iso3 = click_data["points"][0]["location"]
    country_name = click_data["points"][0].get("hovertext", iso3)

    # Get bilateral data for this country in this year
    bilateral = df_bilateral[
        (df_bilateral["reporter_iso3"] == iso3) & (df_bilateral["year"] == year)
    ]

    if bilateral.empty:
        return html.Div([
            html.H3(country_name, style={"margin": "0 0 8px"}),
            html.P(f"No bilateral data for {year}.", style={"color": "#94a3b8"}),
        ])

    # Split by flow
    imports = (
        bilateral[bilateral["flow"] == "Import"]
        .groupby(["partner", "partner_iso3"])["trade_value_usd"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    exports = (
        bilateral[bilateral["flow"] == "Export"]
        .groupby(["partner", "partner_iso3"])["trade_value_usd"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    total_imports = bilateral[bilateral["flow"] == "Import"]["trade_value_usd"].sum()
    total_exports = bilateral[bilateral["flow"] == "Export"]["trade_value_usd"].sum()
    balance = total_exports - total_imports

    def fmt(val):
        if abs(val) >= 1e9:
            return f"${val / 1e9:.1f}B"
        if abs(val) >= 1e6:
            return f"${val / 1e6:.0f}M"
        return f"${val / 1e3:.0f}K"

    def make_bar_chart(data, title, color):
        if data.empty:
            return html.P(f"No {title.lower()} data.", style={"color": "#64748b", "fontSize": "13px"})
        data = data.sort_values("trade_value_usd", ascending=True)
        fig = go.Figure(go.Bar(
            x=data["trade_value_usd"],
            y=data["partner"],
            orientation="h",
            marker_color=color,
            hovertemplate="%{y}: %{x:$.3s}<extra></extra>",
        ))
        fig.update_layout(
            height=max(180, len(data) * 28),
            margin=dict(l=0, r=0, t=4, b=4),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0", size=11),
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False),
        )
        return dcc.Graph(figure=fig, config={"displayModeBar": False},
                         style={"height": f"{max(180, len(data) * 28)}px"})

    balance_color = "#22c55e" if balance >= 0 else "#ef4444"
    balance_label = "surplus" if balance >= 0 else "deficit"

    return html.Div([
        html.H3(f"🏳 {country_name}", style={"margin": "0 0 4px", "fontSize": "20px"}),
        html.P(f"Energy trade in {year}", style={"color": "#94a3b8", "margin": "0 0 12px",
                                                   "fontSize": "13px"}),
        # Summary stats
        html.Div(
            style={"display": "flex", "gap": "12px", "marginBottom": "16px"},
            children=[
                html.Div([
                    html.Div("Imports", style={"fontSize": "11px", "color": "#94a3b8"}),
                    html.Div(fmt(total_imports), style={"fontSize": "18px", "fontWeight": "600",
                                                         "color": "#f97316"}),
                ], style={"flex": "1"}),
                html.Div([
                    html.Div("Exports", style={"fontSize": "11px", "color": "#94a3b8"}),
                    html.Div(fmt(total_exports), style={"fontSize": "18px", "fontWeight": "600",
                                                          "color": "#3b82f6"}),
                ], style={"flex": "1"}),
                html.Div([
                    html.Div("Balance", style={"fontSize": "11px", "color": "#94a3b8"}),
                    html.Div(f"{fmt(balance)} {balance_label}",
                             style={"fontSize": "18px", "fontWeight": "600",
                                    "color": balance_color}),
                ], style={"flex": "1"}),
            ],
        ),
        # Top import sources
        html.H4("Top Import Sources", style={"margin": "0 0 4px", "fontSize": "14px",
                                                "color": "#f97316"}),
        make_bar_chart(imports, "Import", "#f97316"),
        html.Div(style={"height": "12px"}),
        # Top export destinations
        html.H4("Top Export Destinations", style={"margin": "0 0 4px", "fontSize": "14px",
                                                    "color": "#3b82f6"}),
        make_bar_chart(exports, "Export", "#3b82f6"),
    ])


# ── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n  Energy Trade Explorer")
    print("  Open http://127.0.0.1:8050 in your browser\n")
    app.run(debug=True)
