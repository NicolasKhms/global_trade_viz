# Raw Data — Download Instructions

This folder contains the raw UN Comtrade dataset. The file is **not committed to the repository** because of its size.

## How to Download

Use the project's downloader script:

```bash
export COMTRADE_API_KEY="your-key-here"
python -m src.download_comtrade
```

This will fetch HS Chapter 27 (mineral fuels) trade data for all countries,
years 2000–2023, and save it here as `comtrade_energy_trade.csv`.

### Getting a free API key

1. Go to https://comtradedeveloper.un.org
2. Sign up for a free account
3. Subscribe to the **comtrade - v1** product (free tier)
4. Copy your Primary Key from the profile page

### Rate limits (free tier)
- 500 calls/day
- Up to 100,000 records per call

## Expected Schema

Key columns returned by the Comtrade API:

- **reporterDesc** → `reporter` — the reporting country
- **partnerDesc** → `partner` — the trade partner country
- **cmdCode** → `product_code` — HS code (e.g. 2709 for crude oil)
- **cmdDesc** → `product` — human-readable product name
- **flowDesc** → `flow` — Import or Export
- **period** → `year` — trade year
- **primaryValue** → `trade_value_usd` — trade value in USD
