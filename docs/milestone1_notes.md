# Milestone 1 - Report


## Problematic

This project aims to explore how global trade dependencies shape the interconnected structure of the world economy. By analyzing bilateral trade flows across different categories of commodities (energy, agriculture, industrial goods, and possibly more), we investigate the extent to which countries rely on a limited number of partners for essential imports and exports.

Through our visualization, we aim to show how trade relationships are structured across countries, highlighting patterns of concentration, dependency, and diversification. In particular, we focus on identifying which countries are highly dependent on specific partners, which are more diversified, and how these relationships evolve over time across our selected time period. This allows us to better understand potential vulnerabilities in global supply chains and whether global trade is becoming more concentrated or more resilient.

The motivation behind this project is to provide an intuitive and interactive way to understand global trade dynamics, which are often difficult to grasp through raw data alone. By allowing users to explore countries, commodities, and trade partners visually, we aim to make complex trade structures more accessible and interpretable.

The target audience includes students, researchers, and individuals interested in global economics, geopolitics, and commodity markets, as well as anyone seeking to better understand where the goods they consume come from and how countries are interconnected through trade.

---

## Dataset

We use the *UN Comtrade Database*, which provides annual bilateral trade flows (country A's exports to / imports from country B) at the product level (reporter, partner, HS code, flow, trade value in USD). We extract data for **2000–2023**, focusing on **HS Chapter 27** (HS = Harmonized System, an international product classification standard; Chapter 27 covers Mineral Fuels): crude oil, natural gas, coal, LNG (liquefied natural gas), and electrical energy, retrieved via the UN Comtrade API.

*Preprocessing* includes: (1) filtering to HS Chapter 27 and the 2000–2023 window; (2) removing rows with missing reporter, partner, year, or trade value; (3) harmonizing country identifiers to ISO 3166-1 alpha-3 codes (standardized 3-letter country codes, e.g., FRA for France), with a manual override table for non-standard Comtrade name spellings; (4) excluding aggregate entities (e.g., "World", "Areas, nes") from bilateral analysis; (5) constructing aggregated datasets at the country × year and reporter × partner × year levels.

*Data quality* checks confirm: all 393,777 rows have complete core fields; no zero or negative trade values; imports and exports are balanced (50.1% / 49.9%). ISO-3 codes are missing for ~6.2% of reporter rows and ~10.7% of partner rows, mostly due to non-standard names and aggregate entities, addressable with a small manual patch.

*Strengths:* rich bilateral structure; full 24-year time series with no gaps; product-level HS detail; direct compatibility with choropleth mapping libraries (world maps where countries are colored by a variable).

*Limitations:* self-reported data with uneven country coverage; mirror trade asymmetry (country A's reported exports to B do not always match B's reported imports from A); re-exports inflate flows for hub countries (Netherlands, Belgium, Singapore); values in nominal USD with no inflation adjustment; early years (2000–2005) have ~30% fewer reporting countries.

---

## Exploratory Data Analysis

Full analysis is in `notebooks/01_exploratory_data_analysis.ipynb`.

### Dataset Overview

The dataset contains 393,777 rows covering 203 countries, 251 partners, and 2000–2023. Restricting to bilateral flows yields 351,743 rows.

### Global Trade Evolution

Energy trade grew from $0.7T (2000) to $4.0T (2022) (~6× increase). Four key shocks structure the series:

- **2008–09 crisis:** ~35% drop
- **2014–16 oil crash:** sustained decline (shale + OPEC)
- **2020 COVID:** ~25% drop, rapid rebound
- **2022 shock:** peak due to geopolitical supply shifts

Imports and exports closely match → strong data consistency.

### Major Players

- **Importers:** USA, China, Japan, Germany, South Korea, India
- **Exporters:** Russia, Saudi Arabia, Canada, Norway, UAE
- **Dual-role hubs:** USA, Netherlands, Belgium (consumption + re-export)

### Dependency Structure

Energy imports are highly concentrated:

- Many countries source >50% from one partner
- Smaller economies = highest dependency
- Large economies = diversified (low HHI)

→ Key insight: vulnerability vs diversification

### Key Trade Corridors

- Canada → USA (largest globally)
- Russia → EU (pre-2022)
- Gulf → Japan
- Netherlands ↔ Belgium (transit hubs)

### Trade Balance Roles

- **Exporters:** Russia, Saudi Arabia, Norway, Canada
- **Importers:** USA, China, Japan, Germany

→ Clear global producer vs consumer split

### Visualization Readiness

- 181 ISO-3 countries → strong coverage
- 24 years → smooth time slider
- Bilateral structure → Sankey/chord diagrams
- Wide value range → log scale required

### Caveats

- ~15 missing ISO-3 mappings
- Some sparse reporters in early years
- 2023 may be incomplete

---

## Related Work

Several platforms and studies have explored global trade data and its visualization. In particular, the **Observatory of Economic Complexity (OEC)** provides interactive visualizations of international trade flows, allowing users to explore country exports, imports, and product specialization. Similarly, the **World Bank** and **UN Comtrade** offer dashboards and tools to access and visualize trade statistics at a global scale.

While these platforms provide valuable descriptive insights, they often rely on relatively aggregated representations of trade, focusing on total trade values or broad product categories. In contrast, our approach aims to explore trade at a more granular level by leveraging detailed commodity classifications (HS codes). This allows us to capture more precise trade relationships, such as specific energy products, agricultural goods, or industrial materials, and to better understand the structure of global trade flows.

Importantly, our visualization introduces a more interactive, scenario-based perspective. Users will be able to dynamically modify the network for example, by removing a country or trade link, to simulate disruptions and observe how dependencies propagate across the system. Ultimately, this would allow users not only to explore trade patterns, but also to understand the impact of shocks on global supply chains.
