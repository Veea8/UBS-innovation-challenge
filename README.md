# Data Summarization

**UBS Hackathon · Scenario 1 — Ticket Intelligence and Theme Detection**

> From noise to insight: helping risk teams understand what's really going wrong.

Raw tickets → themes → emerging patterns → explainable, actionable insight.
Streamlit dashboard, deterministic clustering, an LLM (OpenAI or Gemini) for the parts
that need language and judgement — grounded, verified, and honest about what it hasn't
seen before.

---

## Start here

**Everyone:** read [`PLAN.md`](PLAN.md), then [`docs/SCHEMA.md`](docs/SCHEMA.md) and
[`docs/GROUNDING.md`](docs/GROUNDING.md), then your own lane doc. About 15 minutes, and it
is the whole coordination overhead.

| You are | Your doc | First thing to do |
|---|---|---|
| Pipeline + app | [LANE_A_PIPELINE.md](docs/LANE_A_PIPELINE.md) | Scaffold + stubs so nobody is blocked |
| **Synthetic data** | [LANE_B_DATA.md](docs/LANE_B_DATA.md) | **Start now** — spec is complete, no dependencies |
| **LLM (OpenAI/Gemini)** | [LANE_C_LLM.md](docs/LANE_C_LLM.md) | Get one call returning parsed JSON |
| **Categories, playbooks + pitch** | [LANE_D_PITCH.md](docs/LANE_D_PITCH.md) | Write `data/categories.json`, then playbooks, then the pitch |

Lanes B and D can start immediately with no code from anyone else. Lane C can start on
parsing, caching and the provider abstraction against the built-in `mock` provider while
we wait for an API key.

## Reference

- [docs/SCHEMA.md](docs/SCHEMA.md) — **the frozen data contracts.** Read before writing code.
- [docs/GROUNDING.md](docs/GROUNDING.md) — **no-hallucination contract**, seed categories,
  seen vs unseen, how confidence is derived. Binding on every lane.
- [docs/SCORING.md](docs/SCORING.md) — signals, risk score, triage gate
- [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) — the 3-minute beat sheet + what's mocked
- [Case_information.md](Case_information.md) — the original brief
- [Ideas.md](Ideas.md) — the brainstorm this came out of

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add an OpenAI or Gemini key (optional: mock provider works offline)
streamlit run app.py
```

Check a data file without running the app:

```bash
python -m core.schema data/tickets.json
```

## The one-line pitch

Deterministic clustering handles the bulk of the volume; the model handles language,
reasoning and novelty. Cost scales with **themes**, not tickets — about twenty calls per
run whether that run covers a thousand tickets or a hundred thousand.

The model works in a closed world: it only ever sees a context block built from our own
tickets and change log, it never searches for a root cause (we correlate deterministically
and hand it a shortlist), and every entity it names is verified against the source data
before it reaches the screen. Problems we have seen before are matched against a seed
category catalog and can be automated. Problems we have not seen are capped below the
automation threshold, and the model is not permitted to state a cause for them at all —
it shows the pattern and hands it to a human expert.

## Synthetic test data summary

The repo includes a deterministic synthetic dataset designed for a root-cause and theme-detection demo. It is intended to simulate a realistic 90-day operational ticket stream and a matching change log.

### Dataset composition

- Tickets: 1,401
- Themes: 11
- Change records: 40
- Time window: 90 days ending 2026-09-22
- Signal mix: 3 planted root-cause themes + 7 background themes + unclustered singletons

### Planted themes

| Theme | Approx. tickets | Purpose |
|---|---:|---|
| `mobile_login_failure_v42` | 258 | Primary hero story: login issues after the mobile roll-out |
| `apac_fx_settlement_recurrence` | 42 | Recurring APAC FX mismatch pattern across 3 episodes |
| `iban_validation_vendor_regression` | 11 | Novel, low-volume Austrian IBAN validation issue |
| `password_reset` | 230 | Common background issue |
| `statement_download` | 150 | Common background issue |
| `card_blocked_abroad` | 140 | Common travel-related background issue |
| `reporting_slow_month_end` | 120 | Monthly operational reporting delay |
| `onboarding_upload` | 110 | Document upload problem |
| `payment_limits` | 130 | Beneficiary / limit query issue |
| `branch_hardware` | 95 | Branch device / printer issue |
| `singleton` | 115 | Genuine one-off tickets that should not cluster |

This keeps the primary story dominant while still preserving realistic noise, decoys, and unclustered edge cases. The ordering matters: S1 is the largest single theme and S3 is the smallest.

### Ticket attributes

Each ticket in [data/tickets.json](data/tickets.json) follows the contract in [docs/SCHEMA.md](docs/SCHEMA.md):

- `ticket_id`: unique incident ID in `INC-` format
- `created_at`: UTC timestamp in ISO 8601 `Z` form
- `channel`: contact channel such as `phone`, `email`, `chat`, `monitoring`, or `branch`
- `region`: `CH`, `EMEA`, `APAC`, or `AMER`
- `business_line`: `Retail`, `Wealth`, `InvestmentBank`, or `Operations`
- `system`: operational system such as `MobileApp`, `eBanking`, `FX-Trading`, `Payments`, `CardServices`, `Onboarding`, or `Reporting`
- `title`: short human-written ticket summary
- `description`: 1–4 sentence human description of the issue
- `reporter_role`: `client`, `client_advisor`, `internal_ops`, or `monitoring_bot`
- `severity_reported`: integer from 1 to 5, where higher means more severe
- `status`: `open`, `in_progress`, `resolved`, or `closed`
- `resolution_notes`: non-null when the ticket has been resolved or closed
- `linked_change_id`: a reference to a change in the change log, or `null`
- `_gt_theme`: hidden ground-truth label used only for evaluation and not for clustering or prompting

### Change attributes

Each record in [data/changes.json](data/changes.json) follows the deployment/change schema:

- `change_id`: change identifier in `CHG-` format
- `deployed_at`: deploy timestamp in UTC ISO 8601 form
- `system`: affected system
- `title`: real-world sounding change title
- `type`: one of `release`, `config`, `infra`, `vendor`, or `certificate`
- `regions`: list of impacted regions
- `owner_team`: owning team or support group
- `rollback_at`: rollback timestamp or `null`

### Why this dataset is useful

This synthetic dataset is designed to force a robust root-cause workflow:

- the main story is not labelled directly for every ticket
- the change log contains decoys and nearby innocent changes
- background noise is realistic and overlaps semantically with the signal themes
- the novel IBAN theme is intentionally hard for keyword-based clustering
- the singleton bucket ensures the system does not force every ticket into a cluster

In practice, this makes the dataset useful for evaluating trend detection, clustering quality, root-cause correlation, and human-review triage decisions.
