# Alpha Hunt India — Makefile
# Single command to reproduce all results: make all

PYTHON = python
SRC    = src
DB     = database/alpha_hunt.db

.PHONY: all setup data universe db strategies tests results paper clean help

all: setup data universe db strategies tests results paper
	@echo "=== Pipeline complete. See results/ and paper/ folders. ==="

# ── Environment ────────────────────────────────────────────────────────────────
setup:
	pip install -r requirements.txt

# ── Data pipeline ──────────────────────────────────────────────────────────────
data:
	$(PYTHON) $(SRC)/data/download.py
	$(PYTHON) $(SRC)/data/ingest.py
	$(PYTHON) $(SRC)/data/clean.py
	$(PYTHON) $(SRC)/data/adjust.py
	$(PYTHON) $(SRC)/data/manifest.py
	@echo "Data pipeline done."

universe:
	$(PYTHON) $(SRC)/universe/fo_universe.py
	@echo "Universe constructed."

# ── Database ───────────────────────────────────────────────────────────────────
db:
	$(PYTHON) database/load.py
	@echo "Database loaded: $(DB)"

# ── Strategies & costs ─────────────────────────────────────────────────────────
strategies:
	$(PYTHON) $(SRC)/strategies/gatev.py
	$(PYTHON) $(SRC)/strategies/pca_ou.py
	$(PYTHON) $(SRC)/ml/ml_strategy.py
	@echo "Strategies computed."

# ── Tests (MUST pass before results) ──────────────────────────────────────────
tests:
	pytest tests/ -v --tb=short
	@echo "All tests passed."

# ── Results ────────────────────────────────────────────────────────────────────
results:
	$(PYTHON) $(SRC)/stats/inference.py
	$(PYTHON) $(SRC)/stats/factor_regression.py
	$(PYTHON) $(SRC)/stats/multiple_testing.py
	$(PYTHON) $(SRC)/stats/subperiod.py
	$(PYTHON) $(SRC)/plots/all_figures.py
	@echo "Results and figures generated."

# ── Paper ──────────────────────────────────────────────────────────────────────
paper:
	cd paper && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
	@echo "Paper compiled: paper/main.pdf"

# ── Utilities ──────────────────────────────────────────────────────────────────
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -f paper/*.aux paper/*.log paper/*.bbl paper/*.blg

hash-check:
	$(PYTHON) $(SRC)/data/manifest.py --verify
	@echo "Hash verification done."

help:
	@echo "make all         — full pipeline"
	@echo "make data        — download and clean data"
	@echo "make universe    — build point-in-time F&O universe"
	@echo "make db          — load data into DuckDB"
	@echo "make strategies  — run all strategies"
	@echo "make tests       — run all placebo and integrity tests"
	@echo "make results     — compute statistics and figures"
	@echo "make paper       — compile LaTeX paper"
	@echo "make hash-check  — verify output reproducibility"
	@echo "make clean       — remove build artefacts"