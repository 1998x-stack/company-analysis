# Sector Scoring v2 — EXPERIMENTAL

This module provides executable industry-specific indicator configurations
for banks, insurers, manufacturers and AI startups. Thresholds and weights
are hypotheses. No empirical calibration, outcome backtesting or external
peer benchmarking has been performed. v1 historical rankings are unchanged.

Usage:

    python3 tools/sector_scoring_v2.py --input path/to/sector_metrics.json

Input shape: sector=<bank|insurance|manufacturing|ai_startup>,
metrics={key: {value: numeric, period: fiscal period, evidence_ids: [id]}}.
Values are fractions/multiples/days/months as documented in the rubric config.

Unreported metrics are marked missing, reduce coverage, and do not count as
bad financial performance. Coverage less than 75% yields no numeric score.
Outputs retain experimental status, sector, period mixture flags and a
leave-one-indicator-out ablation range. Metrics from different sectors must
not be ranked on a shared scale without validated cohort calibration.
