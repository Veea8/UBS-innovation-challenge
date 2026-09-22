# Data Summary

This document summarizes the synthetic operational dataset used for the UBS challenge and explains the important data attributes, patterns, and evaluation logic.

## 1. Dataset overview

- File: `tickets.json`
- File: `changes.json`
- Scope: 90-day synthetic ticket history ending 2026-09-22
- Total tickets: 1,401
- Total change records: 40
- Total themes: 11

The dataset is intentionally designed to resemble a realistic enterprise support backlog with a few strong storylines, a larger set of background operational issues, and a stream of one-off noise cases.

## 2. Ticket-level schema

Each item in `tickets.json` includes the following fields:

- `ticket_id`: unique incident ID in `INC-` format
- `created_at`: timestamp in UTC ISO 8601 format (`Z` suffix)
- `channel`: support channel such as `phone`, `email`, `chat`, `monitoring`, or `branch`
- `region`: one of `CH`, `EMEA`, `APAC`, `AMER`
- `business_line`: one of `Retail`, `Wealth`, `InvestmentBank`, `Operations`
- `system`: one of `eBanking`, `MobileApp`, `FX-Trading`, `Payments`, `CardServices`, `Onboarding`, `Reporting`
- `title`: short human-written ticket title
- `description`: ticket narrative in 1–4 sentences
- `reporter_role`: one of `client`, `client_advisor`, `internal_ops`, `monitoring_bot`
- `severity_reported`: integer 1–5, where 5 is most severe
- `status`: one of `open`, `in_progress`, `resolved`, `closed`
- `resolution_notes`: resolution summary if status is `resolved` or `closed`, otherwise `null`
- `linked_change_id`: linked deployment/change ID if known; otherwise `null`
- `_gt_theme`: ground-truth synthetic label used only for evaluation

### Important note on `_gt_theme`

The field beginning with `_` is evaluation-only metadata. It is not meant to be read by the clustering or scoring pipeline. This allows the project to measure quality without leaking the answer into the same processing step.

## 3. Theme composition

The ticket dataset is built around a realistic mix of signal and noise.

### Planted signal themes

| Theme | Approx tickets | Purpose |
|---|---:|---|
| `mobile_login_failure_v42` | 258 | Main story: login failures after the mobile app 4.2.0 release |
| `apac_fx_settlement_recurrence` | 42 | Three recurring APAC FX settlement mismatch incidents |
| `iban_validation_vendor_regression` | 11 | Slow-burn novel issue with Austrian IBAN validation |

### Background themes

| Theme | Approx tickets | Purpose |
|---|---:|---|
| `password_reset` | 230 | Common locked account / password reset issues |
| `statement_download` | 150 | Statement and document download problems |
| `card_blocked_abroad` | 140 | Card issues while travelling |
| `reporting_slow_month_end` | 120 | Month-end reporting delays |
| `onboarding_upload` | 110 | Document upload failures during onboarding |
| `payment_limits` | 130 | Beneficiary / payment limit errors |
| `branch_hardware` | 95 | Branch printer / device issues |

### Noise and edge cases

| Theme | Approx tickets | Purpose |
|---|---:|---|
| `singleton` | 115 | Unclustered real one-off cases |

This distribution keeps the primary story dominant while preserving realistic operational noise and decoys.

## 4. Root-cause storyline design

The dataset is not just random data. It is intentionally arranged to support a root-cause narrative:

- A legitimate release change (`CHG-0042`) is associated with the main mobile login issue.
- A recurring APAC FX issue (`CHG-0091`) is partially linked to the most recent vendor-related change but not always.
- A novel payment validation issue (`CHG-0103`) is not directly labelled in the ticket stream, making it harder for a simple keyword-based system to identify.

The challenge is to find the pattern through timing, system behavior, region distribution, and evidence correlation rather than looking at a direct label.

## 5. Change log schema

Each item in `changes.json` includes:

- `change_id`: unique change identifier in `CHG-` pattern
- `deployed_at`: UTC deployment timestamp
- `system`: system impacted by the change
- `title`: human-readable change description
- `type`: one of `release`, `config`, `infra`, `vendor`, `certificate`
- `regions`: impacted region list
- `owner_team`: team responsible for the deployment
- `rollback_at`: rollback timestamp or `null`

There are 40 changes total, including:

- 3 planted cause-related changes
- a larger set of decoy and innocent changes designed to challenge correlation logic

## 6. Why this data is useful

This dataset is useful for testing:

- clustering quality and theme grouping
- trend detection over time
- root-cause identification using change correlation
- severity and risk scoring
- ticket triage and playbook matching
- human review vs auto-resolve logic

The synthetic data is realistic enough to look credible while still providing ground-truth labels for evaluation.

## 7. Practical usage

The project can use this data to:

- load and validate tickets from `tickets.json`
- correlate them against changes in `changes.json`
- detect emerging themes and unusual spikes
- rank the likely root causes for human review
- show explainable evidence in a dashboard or app

## 8. Summary

This dataset is a controlled, realistic synthetic operational backlog that supports a challenge around theme detection and root-cause analysis. It balances clear storylines with realistic distractions, making it appropriate for building and evaluating a risk-intelligence workflow.
