<div align="center">

# Alpha Hunt India
### Does Statistical Arbitrage Survive in Indian F&O Markets? (2010–2025)

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-DuckDB-FF6600?style=for-the-badge&logo=duckdb&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-Dashboard-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)
![LaTeX](https://img.shields.io/badge/LaTeX-Research_Paper-008080?style=for-the-badge&logo=latex&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A full-stack quantitative finance project — from raw NSE market data to a published research paper.**

[View Dashboard](#power-bi-dashboard) · [Read the Paper](#research-paper) · [Reproduce Results](#how-to-reproduce)

</div>

---

## The Business Problem

Every day, fund managers and quant traders in India ask a version of the same question:

> *"Is there still money to be made by betting that two similar stocks, which have moved apart, will come back together?"*

This strategy — called **statistical arbitrage** or **pairs trading** — was proven profitable in US markets in the 1990s. But Indian markets are different: higher trading costs, stricter shorting rules through futures, a smaller universe of stocks, and a rapidly changing regulatory environment (including major rule changes in October 2024).

**This project answers that question rigorously** — not with a yes or no, but with exact numbers, honest uncertainty, and a clear cost breakdown. The result is useful whether it says "yes, it works" or "no, it doesn't" — because the methodology and data pipeline are what matter for a real trading desk or research team.

---

## What This Project Demonstrates

| Skill Area | Tools Used | Where in Project |
|---|---|---|
| **Data Engineering** | Python, Pandas, Requests | `src/data/` — NSE bhavcopy ETL pipeline |
| **Data Cleaning** | Pandas, NumPy | Outlier detection, corporate action adjustments |
| **SQL & Analytics** | DuckDB, SQL | `database/queries/` — 10 analytical queries |
| **Machine Learning** | Scikit-learn, LightGBM | `src/ml/` — walk-forward ML strategy |
| **Statistical Inference** | Statsmodels, SciPy | Newey-West t-stats, bootstrap CIs, factor alphas |
| **Data Visualisation** | Power BI (6-page dashboard) | `dashboard/` |
| **Financial Modelling** | Custom Python | Cost model, P&L, Sharpe, drawdown |
| **Academic Research** | LaTeX, verified citations | `paper/` — full IMRaD research paper |
| **Communication** | Gamma AI | `presentation/` — executive deck + report |
| **Reproducibility** | Makefile, pinned deps, seeds | One-command pipeline from raw data |

---

## Project Architecture

```
Raw NSE Data (bhavcopy)
        │
        ▼
┌─────────────────────┐
│  Python ETL Pipeline │  ← src/data/
│  · Ingest (2 formats)│
│  · Clean + validate  │
│  · Adjust for CA     │
│  · Manifest + hashes │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Point-in-time      │  ← src/universe/
│  F&O Universe       │
│  (no hindsight bias)│
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
┌────────┐   ┌─────────────────────┐
│DuckDB  │   │  Strategy Engine    │  ← src/strategies/ + src/ml/
│Database│   │  A: Gatev Pairs     │
│+10 SQL │   │  B: PCA + OU        │
│queries │   │  C: ML Layer        │
└────────┘   └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  Cost Model         │  ← src/costs/
              │  (dated STT + fees) │
              └──────────┬──────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
    ┌──────────────┐      ┌──────────────────┐
    │ Statistics   │      │  Results Tables  │
    │ · NW t-stats │      │  + Figures       │
    │ · Bootstrap  │      │  results/        │
    │ · Factor reg │      └──────────────────┘
    │ · DSR test   │
    └──────────────┘
              │
    ┌─────────┴─────────┐
    ▼                   ▼
┌────────┐      ┌──────────────┐
│Power BI│      │ LaTeX Paper  │
│Dashboard│     │ (25-35 pages)│
│6 pages │      │ + Gamma deck │
└────────┘      └──────────────┘
```

---

## The Three Strategies

### Strategy A — Distance Pairs (Gatev et al. 2006)
The classic approach. Find two stocks that historically moved together. When they diverge by more than 2 standard deviations, bet they will come back together. Simple, transparent, well-studied.

**Parameters:** 12-month formation → 20 best pairs → 6-month trading → enter at ±2σ → exit at zero crossing.

### Strategy B — PCA Factor Residuals (Avellaneda-Lee 2010)
More sophisticated. Use Principal Component Analysis to extract the "market forces" driving all stocks. Look at what's left over (the residual) for each stock. When a stock's residual is unusually far from zero, bet it comes back. Uses an Ornstein-Uhlenbeck model to measure "how stretched" the residual is.

**Parameters:** k=5 PCA factors → 60-day OU fit → s-score entry ±1.25 → exit near zero.

### Strategy C — ML-Enhanced Residuals
Experimental. Take the residuals from Strategy B and train a machine learning model (Ridge, LightGBM, MLP) to predict where they go next. Strict walk-forward validation — model never sees future data. Every prediction is out-of-sample from 2016 onwards.

---

## Data Sources

| Dataset | Source | Period |
|---|---|---|
| NSE Equity Bhavcopy | nseindia.com | 2009–2025 |
| NSE Derivatives Bhavcopy | nseindia.com | 2010–2025 |
| NSE Corporate Actions | nseindia.com | 2009–2025 |
| IIMA 4-Factor Data | iima.ac.in | Oct 1993–2025 |
| Nifty 50 Index | NSE / Yahoo Finance | 2009–2025 |

**Note:** NSE changed its bhavcopy file format around July 2024. The pipeline handles both formats automatically.

---

## Key Results

*(To be filled after analysis is complete — Phase 4)*

| Strategy | Period | Gross Return pa | Net Return pa | Sharpe (net) | Deflated Sharpe |
|---|---|---|---|---|---|
| A: Gatev Pairs | 2010–2025 | TBD | TBD | TBD | TBD |
| B: PCA + OU | 2010–2025 | TBD | TBD | TBD | TBD |
| C: ML Layer | 2016–2025 | TBD | TBD | TBD | TBD |

> All results reported as: "X% per annum, Newey-West t-statistic = Y, net of costs Z% per annum,
> Sharpe = W, deflated Sharpe = V (N strategies in trial registry)."

---

## Power BI Dashboard

Six-page interactive dashboard covering:
- **Market Overview:** F&O universe size over time, ADTV trends, sector composition
- **Strategy Performance:** Cumulative gross vs net returns, rolling Sharpe, drawdown
- **Pairs Deep Dive:** Top pairs heatmap, spread chart, holding period distribution
- **Cost Breakdown:** STT + charges by year, cost sensitivity curve
- **Sub-Period Analysis:** 2010–14, 2015–19, 2020–25 bars; crash episodes
- **ML Signals:** Feature importance, OOS Sharpe timeline

📊 `dashboard/Alpha_Hunt_India_Dashboard.pdf` ← full export

---

## Research Paper

A full academic paper (~25–35 pages, IMRaD structure) is published alongside the code.

**Sections:** Abstract · Introduction · Related Literature · Indian Market Institutional Setting ·
Data · Methods · Results · Robustness · Placebo Tests · Limitations · Conclusion · Appendix

📄 `paper/Alpha_Hunt_India.pdf`

**Important:** This is an out-of-sample extension, not a replication of published numbers.
Results in a different market, different period, different universe will naturally differ.
If the strategies don't work after costs, that is the result — and it is reported plainly.

---

## Presentation

A 10-slide executive deck and a full project report, both created in Gamma AI.

- `presentation/Alpha_Hunt_India_Deck.pdf` — boardroom-ready slide deck
- `presentation/Alpha_Hunt_India_Report.pdf` — full methodology report

---

## Research Integrity

This project was **pre-registered** before any analysis code was written. Every design choice
(parameters, universe rules, cost model, sub-periods, robustness checks) was sealed in
[PREREG.md](PREREG.md) first. Any change made afterwards is logged with a date and reason
in the Deviations section. This prevents cherry-picking results after seeing them.

Every strategy variant run is logged in [trial_registry.csv](trial_registry.csv), and the
Deflated Sharpe Ratio is computed accounting for all trials — not just the best one.

---

## How to Reproduce

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/alpha-hunt-india.git
cd alpha-hunt-india

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download raw data (see DATA_DOWNLOAD.md for manual steps if NSE blocks automated download)

# 4. Run the full pipeline
make all

# Results appear in results/tables/ and results/figures/
# Paper compiles to paper/main.pdf
```

**Single seed, fully deterministic:** every run produces identical outputs (verified by hash check).

---

## Project Structure

```
alpha-hunt-india/
├── PREREG.md              ← pre-registration (sealed before any analysis)
├── config.yaml            ← all parameters in one place
├── trial_registry.csv     ← every experiment logged
├── LIMITATIONS.md         ← honest limitations (written upfront)
├── Makefile               ← make all → full pipeline
├── requirements.txt       ← pinned dependencies
│
├── data/
│   ├── raw/               ← untouched downloaded files (gitignored)
│   └── processed/         ← cleaned, adjusted price series
│
├── src/
│   ├── data/              ← download, ingest, clean, adjust, manifest
│   ├── universe/          ← point-in-time F&O universe construction
│   ├── costs/             ← dated cost model (STT, fees, slippage)
│   ├── strategies/        ← Strategy A (Gatev) and B (PCA+OU)
│   ├── ml/                ← Strategy C (walk-forward ML)
│   ├── stats/             ← inference, factor regression, multiple testing
│   └── plots/             ← all figures
│
├── database/
│   ├── schema.sql         ← relational schema
│   ├── load.py            ← load CSVs into DuckDB
│   └── queries/           ← 10 analytical SQL queries
│
├── tests/                 ← placebo + integrity tests (must pass before results)
├── notebooks/             ← exploration (not used in production pipeline)
│
├── results/
│   ├── tables/            ← all result CSVs
│   └── figures/           ← all charts (PNG)
│
├── dashboard/             ← Power BI .pbix + screenshots + PDF export
├── presentation/          ← Gamma AI deck + report (PDF)
│
└── paper/
    ├── main.tex           ← full LaTeX paper
    ├── refs.bib           ← verified references only
    └── sections/          ← one .tex file per section
```

---

## Limitations

The most important ones (full list in [LIMITATIONS.md](LIMITATIONS.md)):

- This is **not** a replication of published papers — different market, different period
- The Indian F&O universe is small (~100–300 stocks); results are noisier than US studies
- Shorting costs in India (futures-based) are higher than most backtests assume
- NSE bhavcopy data requires careful handling of format changes and corporate actions
- All results are backtests — real execution faces market impact not captured here

---

## References (key sources)

1. Gatev, Goetzmann & Rouwenhorst (2006) — *Review of Financial Studies* — DOI: 10.1093/rfs/hhj020
2. Avellaneda & Lee (2010) — *Quantitative Finance* — DOI: 10.1080/14697680903124632
3. Guijarro-Ordonez, Pelger & Zanotti (2021) — arXiv:2106.04028
4. Harvey, Liu & Zhu (2016) — *Review of Financial Studies* — DOI: 10.1093/rfs/hhv059
5. Agarwalla, Jacob & Varma — IIMA Indian 4-Factor Data Library

Full bibliography in `paper/refs.bib` — every entry has a verified DOI or arXiv ID.

---

<div align="center">

Built with rigour, honesty, and a genuine curiosity about whether this works.

</div>
