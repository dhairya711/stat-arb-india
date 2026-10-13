# Institutional Pitch Deck: Statistical Arbitrage in Indian F&O Stocks (2010–2025)
*Ready-to-Import Format for Gamma App / Pitch Decks*

---

## Slide 1: Executive Title & Core Business Problem
**Title:** The Microstructure Mirage: Does Statistical Arbitrage Survive in Indian F&O Stocks?  
**Subtitle:** Methodological Replication, ML Extensions, and the Anatomy of Transaction Cost Erosion (2010–2025)  
**Presenter:** Dhairya Dani (VIT Bhopal) | Quantitative Finance & Machine Learning  
**Target Audience:** Chief Investment Officers, Quant Desk Heads, Institutional Allocators  

**The Multi-Crore Problem Statement:**
- Quantitative teams frequently present backtests showing Sharpe ratios above 1.5 in mean-reverting equity pairs.
- Yet, when deployed in Indian derivatives markets, these strategies systematically bleed capital.
- **The Core Question:** Is the alpha genuine but annihilated by Indian transaction costs (STT, stamp duty, turnover fees, GST, slippage), or was it an artifact of backtest overfitting?

---

## Slide 2: Universe & Data Infrastructure
**Strict Institutional Data Architecture:**
- **Sample Period:** 16 Calendar Years (January 1, 2010 – December 31, 2025).
- **Universe Definition:** Point-in-time NSE F&O permitted equity list (~140 to 215 stocks dynamically varying across time).
- **Survivorship-Bias Elimination:** Companies delisted, barred, or removed from F&O are retained in historical cross-sections until expulsion date.
- **Corporate Action Precision:** Backward cash-dividend, bonus, and split adjustments verified against historical INFY, TCS, and RELIANCE benchmark corporate events.
- **Analytics Database:** Local high-performance DuckDB columnar warehouse (`database/stat_arb.duckdb`) handling over 200,000 strategy-day records.

---

## Slide 3: Three Methodological Quant Frameworks
**1. Distance Pairs (Gatev, Goetzmann, Rouwenhorst 2006):**
- 252-day formation window minimizing sum of squared differences (SSD) on normalized cumulative return series.
- Top 20 pairs traded during 126-day trading windows with 2.0σ entry, committed capital allocation, and 1-day wait execution lag.

**2. PCA-Residual Mean Reversion (Avellaneda & Lee 2010):**
- Rolling 252-day PCA factor extraction ($k=5$ statistical factors).
- Cross-sectional residual regression and rolling 60-day Ornstein-Uhlenbeck (OU) AR(1) process estimation.
- Dimensionless $s$-score trading with dollar-neutral market balance and 10% position caps.

**3. ML-Enhanced Residual Reversion (Guijarro-Ordonez et al. 2021 echo):**
- Expanding-window walk-forward machine learning (Ridge regression, HistGBM, MLP) predicting 5-day ahead residual mean-reversion.
- 10-day strict embargo purge between training and test sets to eliminate autoregressive lookahead leakage.
- Long top quintile, short bottom quintile dollar-neutral portfolio rebalancing.

---

## Slide 4: Empirical Findings: The Gross Alpha Illusion
**Empirical Performance Across Models (2010–2025):**

| Strategy Framework | Gross Sharpe (0.0x Cost) | Newey-West HAC t-stat | Net Sharpe (1.0x Institutional) | Net Max Drawdown |
| :--- | :---: | :---: | :---: | :---: |
| **Strategy A: Gatev Distance Pairs** | **+0.95** | **+4.11** | **-2.50** | **-98.57%** |
| **Strategy B: Avellaneda-Lee PCA-OU** | **+1.28** | **+7.49** | **-1.62** | **-95.06%** |
| **Strategy C: ML-Enhanced Residuals** | **+1.54** | **+4.05** | **-2.96** | **-98.72%** |

**The Stark Takeaway:**
- Gross alpha is undeniably real and statistically significant ($t > 4.0$).
- Net returns under institutional friction are universally negative. The strategy is an unviable standalone business under standard trading frequencies.

---

## Slide 5: The Anatomy of Indian F&O Friction
**Where Does the Alpha Disappear?**
- **Securities Transaction Tax (STT):**
  - Historical: 0.0125% on sell side (Futures).
  - Effective October 1, 2024: Increased by 60% to **0.0200%** under SEBI derivatives containment regulations.
- **Exchange & Regulatory Charges:**
  - NSE Transaction Charges: 0.0019% (blended).
  - SEBI Turnover Fee: 0.0001%.
  - Stamp Duty: 0.0020% (buy side).
  - GST: 18% on brokerage and exchange charges.
- **Execution Slippage:** Tiered market-impact model (2 to 10 bps based on ADTV tier).
- **The Killing Threshold:**
  - Breakeven cost multiplier is **0.38x** of baseline.
  - A quant fund must achieve sub-5 bps all-in round-trip execution to break even—impossible without designated market-maker rebates.

---

## Slide 6: Machine Learning Feature Attribution
**What Actually Predicts Residual Reversion in Indian Equities?**
1. **Residual OU Mean Reversion Speed ($\kappa$):** 38.4% Importance — High kappa speeds strongly predict rapid convergence before expiration.
2. **Standardized Residual Z-Score ($s$-score):** 27.1% Importance — Magnitude of displacement provides the core statistical spring.
3. **Idiosyncratic Volatility ($\sigma_{eq}$):** 16.5% Importance — High noise reduces pair predictability.
4. **Liquidity Spread / Bid-Ask Proxy:** 11.2% Importance — Wider spreads correlate with phantom mispricings that cannot be monetized.
5. **Cross-Sectional Momentum Lag:** 6.8% Importance.

**Key Insight:** Complex non-linear models (MLP, GBM) suffer higher turnover without generating enough excess gross return to offset incremental trading friction. Linear Ridge regularization dominates.

---

## Slide 7: Macro Regime Stress Testing & Crash Behavior
**Stress Testing Across Four Extreme Market Regimes:**
1. **COVID-19 Crash (Feb–Mar 2020):**
   - Gross Sharpe spiked to +3.12 as spreads blew out.
   - Net performance suffered massive divergence losses as cointegration broke down across several stressed industrial pairs.
2. **Demonetisation Shock (Nov–Dec 2016):**
   - Sector-wide divergence (Banking & Real Estate vs IT/Pharma); rapid recovery within 45 trading days.
3. **2022 Inflation & Rate Hike Selloff:**
   - Prolonged low-volatility trend drift led to slow bleeding and pair timeouts.
4. **Post-SEBI STT Hike Regime (Oct 2024–2025):**
   - Margin requirements and doubled STT increased annual cost drag by 140 bps, permanently extinguishing marginal pair viability.

---

## Slide 8: Enterprise Analytics Engine: DuckDB & Advanced SQL
**Production SQL Capabilities:**
- Full relational audit trail in DuckDB (`stat_arb.duckdb`).
- **10 Parameterized Production Analytical Queries:**
  - `q01`: Top 10 Pairs by Sharpe per calendar year.
  - `q02`: 12-Month rolling PnL and cumulative equity curves.
  - `q03`: Year-over-Year F&O Universe turnover and survivorship drift.
  - `q04`: Annual institutional friction anatomy (bps decomposition).
  - `q05`: Peak-to-trough maximum drawdown identification.
  - `q06`: Sub-period performance across pre-registered eras (SP1, SP2, SP3).
  - `q07`: Stress-period return attribution.
  - `q08`: Correlation with IIMA 4-factor risk benchmarks.
  - `q09`: Trade duration and holding distribution quartiles.
  - `q10`: Parametric cost sensitivity matrix (0.0x, 0.5x, 1.0x, 1.5x).

---

## Slide 9: Power BI Executive Dashboard Architecture
**Star-Schema Dimensional Reporting:**
- **Page 1: Executive KPI Overview:** High-level summary of gross vs net divergence, capital drag, and breakeven boundaries.
- **Page 2: Strategy Comparative Matrix:** Cross-strategy side-by-side evaluation across Gatev, PCA, and ML.
- **Page 3: Microstructure Friction Waterfall:** Interactive breakdown of each tax, exchange, and slippage component.
- **Page 4: Sub-Period & Macro Regime Matrix:** Deep-dive into performance during stress episodes.
- **Page 5: Machine Learning Diagnostics:** Walk-forward stability, feature importances, and quintile spreads.
- **Page 6: Risk Attribution & Factor Exposure:** Fama-French/IIMA factor betas and market neutrality verification.

---

## Slide 10: Institutional Recommendations & Future Outlook
**Strategic Imperatives for Indian Asset Managers:**
1. **Abandon Standalone Daily Stat-Arb:** Do not allocate risk capital to daily statistical arbitrage in Indian single-stock F&O expecting standalone alpha.
2. **Repurpose as Execution Overlay:** Residual signals are highly valuable as execution alpha (timing trade entry/exit for long-only or fundamental portfolios to capture 15–30 bps of spread).
3. **Extend Holding Horizons:** Shift from 5–20 day residual mean-reversion to 60–120 day structural cointegration to dilute per-trade turnover costs.
4. **Demand Proprietary Tiered Access:** Viable implementation requires co-located DMA access, zero-brokerage arrangements, and liquidity-provider rebate status.
