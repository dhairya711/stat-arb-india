-- database/schema.sql
-- DuckDB schema for Alpha Hunt India
-- All tables are populated by database/load.py

-- ── Raw equity prices (adjusted) ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS prices (
    symbol          VARCHAR NOT NULL,
    trade_date      DATE    NOT NULL,
    open            DOUBLE,
    high            DOUBLE,
    low             DOUBLE,
    close           DOUBLE,
    adj_close       DOUBLE,
    adj_factor      DOUBLE,
    volume          BIGINT,
    traded_value_lakh DOUBLE,
    adtv_cr_252d    DOUBLE,
    daily_return    DOUBLE,
    adj_return      DOUBLE,
    series          VARCHAR,
    isin            VARCHAR,
    PRIMARY KEY (symbol, trade_date)
);

-- ── F&O universe membership (point-in-time) ───────────────────────────────────
CREATE TABLE IF NOT EXISTS universe (
    symbol          VARCHAR NOT NULL,
    trading_month   VARCHAR NOT NULL,   -- YYYY-MM format
    adtv_cr         DOUBLE,
    missing_days    INTEGER,
    in_universe     BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (symbol, trading_month)
);

-- ── Corporate actions ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS corporate_actions (
    symbol          VARCHAR,
    ex_date         DATE,
    purpose         VARCHAR,
    ratio           VARCHAR,
    adj_factor      DOUBLE,
    verified        BOOLEAN DEFAULT FALSE
);

-- ── Strategy signals ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS signals (
    strategy        VARCHAR NOT NULL,  -- A, B, C
    signal_date     DATE    NOT NULL,
    symbol          VARCHAR NOT NULL,
    signal_type     VARCHAR,           -- LONG, SHORT, CLOSE
    spread          DOUBLE,
    s_score         DOUBLE,
    kappa           DOUBLE,
    cohort_id       VARCHAR,           -- for Strategy A
    partner_symbol  VARCHAR,           -- for Strategy A
    trial_id        VARCHAR,
    PRIMARY KEY (strategy, signal_date, symbol, cohort_id)
);

-- ── Trades (filled signals) ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS trades (
    trade_id        VARCHAR PRIMARY KEY,
    strategy        VARCHAR,
    trial_id        VARCHAR,
    symbol          VARCHAR,
    partner_symbol  VARCHAR,
    open_date       DATE,
    close_date      DATE,
    holding_days    INTEGER,
    gross_return    DOUBLE,
    cost_bps        DOUBLE,
    cost_multiplier DOUBLE,
    net_return      DOUBLE,
    open_signal     VARCHAR,
    close_signal    VARCHAR,
    notional_inr    DOUBLE,
    adtv_cr         DOUBLE
);

-- ── Daily strategy returns ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS strategy_returns (
    strategy        VARCHAR NOT NULL,
    trial_id        VARCHAR NOT NULL,
    return_date     DATE    NOT NULL,
    gross_return    DOUBLE,
    net_return      DOUBLE,
    cost_multiplier DOUBLE,
    n_open_pairs    INTEGER,
    capital_method  VARCHAR,
    PRIMARY KEY (strategy, trial_id, return_date, cost_multiplier)
);

-- ── Factor data (IIMA 4-factor) ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS factors (
    factor_date     DATE PRIMARY KEY,
    mkt             DOUBLE,
    smb             DOUBLE,
    hml             DOUBLE,
    wml             DOUBLE,
    rf              DOUBLE    -- risk-free rate (91-day T-bill)
);

-- ── Nifty 50 index ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nifty50 (
    trade_date      DATE PRIMARY KEY,
    close           DOUBLE,
    daily_return    DOUBLE
);

-- ── Trial registry ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS trial_registry (
    trial_id        VARCHAR PRIMARY KEY,
    date_run        DATE,
    strategy        VARCHAR,
    variant_id      VARCHAR,
    description     VARCHAR,
    gross_sharpe    DOUBLE,
    net_sharpe      DOUBLE,
    gross_return_pa DOUBLE,
    net_return_pa   DOUBLE,
    nw_tstat        DOUBLE,
    dsr             DOUBLE,
    notes           VARCHAR
);
