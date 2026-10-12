# LIMITATIONS

This document was written BEFORE any results were seen, as a commitment to honest reporting.

## 1. Not a Replication of Published Numbers
This project applies Gatev et al. (2006) and Avellaneda-Lee (2010) methodology to
Indian F&O stocks. We use a different market, different universe, and different period.
We NEVER claim to replicate the published performance numbers.

## 2. Survivorship and Universe Construction
- F&O universe is constructed from NSE derivatives bhavcopy month-by-month.
- Despite point-in-time construction, subtle biases may remain (e.g., stocks added
  to F&O tend to be larger/more liquid, introducing an implicit quality filter).
- Data gaps and format changes (NSE changed bhavcopy format ~July 2024) may cause
  some stocks to be incorrectly included or excluded.

## 3. Small Cross-Section
The Indian F&O universe (100-300 stocks over the period) is much smaller than the
US CRSP universe used by Gatev. Fewer pairs = less diversification = noisier results.
The small universe also limits the statistical power of the ML layer.

## 4. Lot-Size and Capital Constraints
NSE F&O has minimum lot sizes. Many signals will not be tradeable at small capital
sizes in whole lots. We report the minimum capital required and flag infeasible cases.
This limits the real-world applicability for small accounts.

## 5. Cost Model Uncertainty
The cost model uses estimates for some components (slippage, pre-2024 exchange charges,
SEBI turnover fee). Actual costs depend on broker, account size, and execution quality.
Sensitivity analysis across cost multipliers (0-150%) partially addresses this.

## 6. Shorting Constraints
Multi-day shorts in India require single-stock futures. The futures market has:
  - Lot-size constraints (capital requirements)
  - Roll costs at monthly expiry
  - Potential illiquidity in far-month contracts
  - Possible squeeze risk in individual stocks
These factors are partially modelled but not fully captured.

## 7. ML Overfitting Risk
Strategy C uses a small cross-section and expanding walk-forward. Despite regularisation
and out-of-sample evaluation, the ML model may have latent overfitting not detected by
standard tests. The deflated Sharpe ratio partially corrects for this.

## 8. Data Format Changes
NSE changed its bhavcopy format around July 2024. Automated parsing covers both formats,
but edge cases at the transition may exist. The data quality report documents all flags.

## 9. Factor Data Coverage
IIMA 4-factor data starts from October 1993. It is available for the full sample period
(2010-2025). If any months are missing, analysis truncates honestly and documents gaps.

## 10. No Real Execution
All results are backtests. Real execution faces:
  - Market impact beyond our slippage model
  - Execution latency
  - Order rejection / partial fills
  - Short-selling bans (India has imposed temporary bans historically)
