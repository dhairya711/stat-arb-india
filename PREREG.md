# PRE-REGISTRATION DOCUMENT
**Project:** Alpha Hunt India — Does Statistical Arbitrage Survive in Indian F&O Stocks?
**Pre-registration date:** 2026-10-12
**Status:** SEALED. All design choices below are fixed before any analysis code is run.
**Post-seal changes go ONLY in Section 12 (Deviations Log) with date + reason.**

---

## 0. FRAMING

This is a methodological replication and out-of-sample extension — NOT a replication of
published numbers. Different market (India), different universe (NSE F&O stocks), different
period (2010-2025). We NEVER claim to replicate Gatev et al. (2006) tables.

Strategy C ML layer is a simplified echo of Guijarro-Ordonez, Pelger & Zanotti (2021,
arXiv:2106.04028). We do NOT claim to replicate that paper.

Sample period: 2010-01-01 to 2025-12-31. Warmup data (2009) used only inside formation
windows and explicitly documented.

---

## 1. RESEARCH QUESTIONS

RQ1: Does the Gatev distance strategy earn positive returns in Indian F&O stocks
     in 2010-2025, gross AND net of costs?
RQ2: Does PCA-residual mean reversion (Avellaneda-Lee style) outperform?
RQ3: Does an ML layer on PCA-residual features add out-of-sample value net of costs?
RQ4: How do results vary by sub-period, volatility regime, and crash episodes?
RQ5: How sensitive are net results to cost assumptions? What is the break-even cost?

---

## 2. HYPOTHESES

H1: Strategy A gross return > 0 over full period
H2: Strategy A net return > 0 after baseline costs
H3: Strategy B Sharpe > Strategy A Sharpe (full period)
H4: Strategy C net Sharpe > Strategy B net Sharpe (2016-2025 window)
H5: All strategies show lower returns post-2018 (decay hypothesis)
H6: Strategy A gross return positive in sub-period SP1 (2010-2014)

Null/negative result on any hypothesis will be reported plainly.

---

## 3. SURVIVAL DEFINITION

SURVIVES: Net annualised excess return > 0, Newey-West t-stat > 1.65, AND
          Deflated Sharpe Ratio > 0; for primary spec over full period.

DOES NOT SURVIVE: Net return <= 0, OR t-stat <= 1.65, OR DSR <= 0.
Gross-only positives with negative net DO NOT count as survival.

---

## 4. VERIFIED STRATEGY PARAMETERS

### 4A. Gatev et al. (2006) — DOI: 10.1093/rfs/hhj020 — VERIFIED

| Parameter              | Paper Value                                      | Status    |
|------------------------|--------------------------------------------------|-----------|
| Formation period       | 12 months (252 trading days)                     | VERIFIED  |
| Trading period         | 6 months (~126 trading days)                     | VERIFIED  |
| Universe               | All CRSP NYSE/AMEX stocks; no sector restriction | VERIFIED  |
| Pair metric            | Sum of squared deviations; normalised to 1.0     | VERIFIED  |
| Top N primary          | Top 20 pairs by minimum SSD                      | VERIFIED  |
| Top N secondary        | Top 5 pairs                                      | VERIFIED  |
| Entry threshold        | 2 formation-period sigma of spread               | VERIFIED  |
| Exit rule              | Spread crosses zero OR end of trading period     | VERIFIED  |
| Reopening              | Pair may reopen within same trading period       | VERIFIED  |
| Cohort structure       | Monthly; 6 overlapping cohorts active at once   | VERIFIED  |
| Primary capital def    | Committed capital (full 6-month period)          | VERIFIED  |
| Secondary capital def  | Fully invested capital (active days only)        | VERIFIED  |
| One-day wait           | Variant tested; not main spec                    | VERIFIED  |
| Sector restriction     | Robustness only; not main spec                   | VERIFIED  |

### 4B. Avellaneda & Lee (2010) — DOI: 10.1080/14697680903124632 — PARTIALLY VERIFIED

| Parameter              | Our Value (Paper)                                | Status         |
|------------------------|--------------------------------------------------|----------------|
| PCA window             | 252 rolling days                                 | VERIFIED       |
| PCA factors k          | k=5 main spec (paper uses eigenvalue threshold)  | UNVERIFIED exact|
| OU window              | 60 rolling days                                  | VERIFIED       |
| s-score formula        | s = (X_t - mu) / sigma_eq                       | VERIFIED       |
| Open long              | s < -1.25                                        | VERIFIED       |
| Open short             | s > +1.25                                        | VERIFIED       |
| Close long             | s > -0.5                                         | VERIFIED       |
| Close short            | s < +0.75                                        | VERIFIED       |
| Kappa filter           | kappa > 1/252 annualised (paper exact UNVERIFIED)| UNVERIFIED exact|
| Dollar neutral         | true                                             | VERIFIED       |

---

## 5. UNIVERSE RULES (POINT-IN-TIME)

- Stock in universe for month M if: >= 15 trading days SSF data in month M (derivatives bhavcopy)
- Universe built using only data available by end of prior month (no look-ahead)
- Liquidity filters over 252-day formation window:
  - ADTV >= INR 10 crore (param: min_adtv_cr)
  - Missing trading days <= 10 (param: max_missing_days)
  - Price >= INR 10 throughout formation window
- Delisted / F&O-discontinued stocks included up to last active date (no survivorship bias)
- Annual entry/exit counts: results/tables/universe_coverage.csv

---

## 6. COST MODEL (DATED SCHEDULE)

STT on futures (VERIFIED — Union Budget 2024-25, NSE circular):
  Before 2024-10-01: 0.0125% of traded value (sell side)
  From   2024-10-01: 0.0200% of traded value (sell side)

NSE exchange charges per INR 1 lakh traded value:
  From   2024-10-01: INR 1.73 (VERIFIED — NSE circular Oct 2024)
  Before 2024-10-01: INR 1.90 placeholder (UNVERIFIED — confirm from NSE archive)

Other (UNVERIFIED — to verify at sebi.gov.in before paper):
  SEBI turnover fee: 0.0001% of turnover
  Stamp duty: 0.002% buyer side (state-dependent)
  GST: 18% on brokerage + exchange charges
  Brokerage: INR 20 per order (discount broker, parameterised)

Slippage (model assumptions):
  Tier 1 (ADTV > INR 100cr): 2 bps per side
  Tier 2 (ADTV 20-100cr):    5 bps per side
  Tier 3 (ADTV 10-20cr):    10 bps per side

Futures roll: 5 days before expiry; 5 bps round-trip default (to update with basis data)
Margin: 15% of notional (SPAN + exposure; parameterised)
Report returns on: committed capital AND margin capital

Cost scenarios: 0%, 50%, 100%, 150% of baseline; break-even cost per trade reported.

---

## 7. SUB-PERIODS

SP1: 2010-01-01 to 2014-12-31 (early period)
SP2: 2015-01-01 to 2019-12-31 (mid period)
SP3: 2020-01-01 to 2025-12-31 (COVID, recovery, 2024 reforms)

Crash/regime episodes:
  COVID crash:      2020-02-19 to 2020-03-31 (Nifty drawdown > 35%)
  Demonetisation:   2016-11-08 to 2016-12-31
  2022 selloff:     2022-01-01 to 2022-06-30
  Post-SEBI 2024:   2024-10-01 to 2025-12-31

Regime: high vs low volatility by Nifty 50 realised monthly vol above/below full-period median.

---

## 8. STATISTICAL TESTS

- Newey-West t-stat: lag = floor(4*(T/100)^(2/9)) [Andrews rule]
- Stationary bootstrap CIs: B=1000, mean block = 5 months [Politis-Romano 1994]
- Factor regressions: CAPM; IIMA 4-factor (MKT,SMB,HML,WML); Newey-West SEs; monthly
- Multiple testing: Deflated Sharpe Ratio [Harvey-Liu-Zhu 2016]; White's Reality Check
- All variants logged in trial_registry.csv; DSR deflated by full trial count

---

## 9. ROBUSTNESS CHECKS (ONLY THESE — PRE-REGISTERED)

R1:  Top 5 vs top 20 pairs                          [A]
R2:  One-day wait after signal                       [A]
R3:  Sector-restricted pair matching                 [A]
R4:  PCA factors k=3                                 [B]
R5:  PCA factors k=8                                 [B]
R6:  Entry threshold s=+-2.0                         [B]
R7:  Cost multiplier 0%, 50%, 150%                   [A,B,C]
R8:  Exclude 2020 COVID crash months                 [A,B,C]
R9:  Spot-based P&L vs futures-based P&L             [A,B]
R10: Liquid-only subset (ADTV > INR 50cr)            [A,B,C]
R11: Target horizon 1 day (vs 5 day)                 [C]
R12: Fixed 5-year walk-forward windows               [C]

Any check NOT on this list needs a Deviations entry + approval before running.

---

## 10. PLACEBO AND INTEGRITY TESTS (ALL MUST PASS BEFORE VIEWING RESULTS)

PL1: Cointegrated pair detection — planted I(0) pairs found; ADF rejects unit root
PL2: Random-walk pair placebo — abs(t) < 1.65 over 1000 sims of random pairs
PL3: No look-ahead — signal shifted -1 day inflates Sharpe; +1 day does not
PL4: ML permutation — shuffled predictions give net Sharpe ~= 0 (100 permutations)
PL5: Reproducibility — make all from data/raw gives identical table hashes
PL6: OU synthetic — simulated OU series traded by s-score: positive mean return before costs

---

## 11. VERIFIED REFERENCES

1.  Gatev et al. (2006)           DOI: 10.1093/rfs/hhj020          VERIFIED
2.  Avellaneda & Lee (2010)       DOI: 10.1080/14697680903124632    VERIFIED
3.  Guijarro-Ordonez et al. (2021) arXiv: 2106.04028               VERIFIED
4.  Harvey, Liu, Zhu (2016)       DOI: 10.1093/rfs/hhv059          VERIFIED
5.  McLean & Pontiff (2016)       DOI: 10.1111/jofi.12365          VERIFIED
6.  Gu, Kelly, Xiu (2020)         DOI: 10.1093/rfs/hhaa009         VERIFIED
7.  Do & Faff (2010)              DOI: 10.2469/faj.v66.n4.1        VERIFIED
8.  Agarwalla, Jacob, Varma       IIMA FF factors; iima.ac.in       VERIFIED (from Oct 1993)
9.  Politis & Romano (1994)       DOI: 10.1080/01621459.1994.10476870  VERIFIED
10. Newey & West (1987)           DOI: 10.2307/1913610              VERIFIED
11. White (2000)                  DOI: 10.1111/1468-0262.00152      VERIFIED

UNVERIFIED (cannot add to .bib until located):
- SEBI F&O trader profitability study (title/year/report number TBD)
- India-specific pairs/momentum studies (to be found via literature search)

---

## 12. DEVIATIONS LOG

| Date   | Section | Change | Reason |
|--------|---------|--------|--------|
| (none) | —       | No deviations at sealing | — |
