# Company Analysis Factory — Architecture v2 Proposal

Status: RFC. This document describes the target architecture; most v2 components
are NOT implemented yet. The current published catalog is a legacy v1 snapshot.

## 1. Goals and non-goals

Goals:
- Reproduce every evaluation from its persisted evidence, indicator levels and rubric version.
- Keep company identity separate from brand, ticker, legal entity and report filename.
- Compare companies within appropriate sector-specific cohorts and accounting conventions.
- Publish all search, ranking and industry views from one canonical structured dataset.
- Make AI-assisted research reviewable; flag uncertain or contradictory evidence.
- Preserve existing Markdown reports and historical scores without silent rewriting.

Non-goals for this quality-foundation PR:
- Modifying the historical 230 company scores.
- Claiming that private company revenue estimates or online rumors are audited facts.
- Automatically trading securities or declaring any employer safe to join.
- Installing a paid database, running live crawling, or deploying an API service.

## 2. Current state

Source of truth today: docs/companies.json for the website, docs/examples for
reports and radar assets, and company/ symlinks for industry navigation.
The fixed-weight scoring engine lives under .claude/skills/company-health-eval.
The frontend is static, loading docs/companies.json and Markdown via fetch.
There are 230 catalog entries, 22 industries and 117 subindustries.

Known legacy inconsistencies include grade boundaries computed on rounded
scores, imprecise score reconstruction, sector-path drift and chart basename
collisions. An audit reports rather than silently repairing these cases.

## 3. Target pipeline

DISCOVER → COLLECT → EXTRACT → VERIFY → NORMALIZE → SCORE → REVIEW
        → REPORT → PUBLISH → MONITOR → RE-EVALUATE

Each step must be idempotent and versioned, and write a machine-readable stage
manifest with input hashes, output hashes, sources, runtime and error details.
An evaluation must be explicitly reviewed before publication.

## 4. Versioned entities and invariants

company:
  company_id: immutable, globally unique slug/UUID
  legal_entity_ids: optionally multiple; company group and subsidiaries differ
  names: official, English, aliases
  tickers: exchange-qualified with effective time intervals
  industry: taxonomy_id and taxonomy_version
  visibility: public or private, with separate disclosure policies

evidence:
  evidence_id: source URL + retrieval timestamp + content hash
  publisher, primary_or_secondary, document_date, reporting_period
  retrieved_at, currency, units, fiscal_calendar
  source_excerpt, page/table/line location, license/access considerations
  reliability and contradictions, not merely a confidence adjective

observation:
  company_id, metric_id, value, unit, currency, period, scope, evidence_ids
  type: reported / estimated / calculated / disputed / unavailable
  formula_version, assumption_version, interval when estimated
  missingness_reason (not disclosed / not applicable / failed retrieval)

evaluation:
  evaluation_id, company_id, as_of_date, sector_rubric_version
  evidence_snapshot_ids, source_data_hash, indicator_assessments
  inputs, dimension_scores_unrounded, total_unrounded, display_total
  coverage, uncertainty, reviewer, status (draft/reviewed/published)
  code_commit, model_name and prompt_version when AI assisted

IMPORTANT: Unknown != poor performance. Missing data must lower confidence or
coverage, not automatically assign a distressed-risk score.

## 5. Rubric governance

Keep v1 as frozen score_v1, preserve reproducibility, and backtest v2 before
switching any production ranking or grade. Split:
- Financial resilience: liquidity, earnings quality, leverage, cash conversion
- Competitive position: unit economics, growth, moat, customer concentration
- Employer suitability: compensation, team, legal disputes, management, role fit
- Valuation (optional): market price relative to fundamentals; NOT employer score

Different cohorts require distinct metrics and benchmark rules:
- Banks: capital adequacy, asset quality, deposits, liquidity, NIM, provisioning.
- Insurers: solvency, investment assets, claims, NBV, embedded value.
- Manufacturing: working capital, capex, cycle, inventory, debt, utilization.
- SaaS/software: retention, ARR, gross margin, cash burn, deferred revenue.
- Biotech/pre-revenue: runway, trial pipeline, milestones, dilution, R&D.
- Real estate: presales, funding maturity wall, projects, contracted backlog.
- Government institutions: research funding and stability, not corporate FCF.

Industry percentile comparisons must always show cohort size, metric definition,
fiscal-period comparability, and uncertainty. Do not compare unrelated sectors
as though their absolute financial scores have identical meanings.

## 6. Data architecture and publication

Suggested layout (future):
  src/company_analysis/{collectors,extract,normalize,scoring,reporting,publishing}
  schemas/{company,evidence,observation,evaluation}.json
  data/{raw,normalized,indicator_inputs,evaluations}/
  docs/examples/ ... legacy reports remain
  frontend/ ... static or hybrid deployment

A single canonical evaluation snapshot feeds:
  companies.json, Markdown report, radar/SVG, ranking, industry index and website.
Never hand-edit the same score independently across multiple outputs.
Use atomic, repeatable generation with manifest and checksum validation.

## 7. Agent architecture

A coordinator delegates bounded jobs to:
  source_searcher → document_reader → financial_extractor
  → cross_checker → rubric_assessor → critique_agent → report_writer
Humans review high-impact assertions and conflicts. Use structured tool inputs
and outputs, citation spans and explicit retries; do not infer truth merely
because several AI agents agree.

## 8. Quality gates and acceptance

P0 (this branch): read-only audit, baseline tests, frontend safety/correctness,
and the Longsys case-sensitive PNG reference fix. No score migration.

P1: preserve scoring inputs for every new report, link evidence to each metric,
apply JSON Schema checks, add CI reports and build scripts.
Acceptance: 100% references resolve; new outputs reproduce bit-for-bit apart
from documented timestamps; every hard claim has a traceable source.

P2: sector rubrics and uncertainty-aware grades in versioned experiments.
Acceptance: public benchmark, error analysis, sensitivity to missing metrics,
historical replay, inter-annotator agreement and ablation tests.

P3: tracked agent workflow, state store and incremental refreshing.
Acceptance: idempotent restarts, no duplicate evaluations, recoverable partial
failures and an evaluation review queue.

P4: frontend UX, search, comparisons and analytics.
Acceptance: accessible mobile UX, filtering with denominators, stable URLs,
data freshness indicators, source drilldown and independent E2E tests.

## 9. Operational controls

- Never write directly to master; use a reviewable PR and CI.
- No score, company identity or source URL may be silently changed by a formatter.
- Do not publish unsupported allegations as verified facts.
- Distinguish retrieval date from underlying reporting period.
- Cache licensed sources only where usage terms permit.
- Use time-stamped assessments; never present historical data as live.
- Publish audit warnings with an explicit remediation owner and deadline.
