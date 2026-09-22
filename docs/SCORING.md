# SCORING — signals, risk score, triage gate

Owned by Lane A, but **everyone should understand this page** — it is what a judge will
probe in Q&A, and Lane D has to explain it in 20 seconds on stage.

Two design principles:

1. **No number appears on screen without its components.**
2. **Risk is computed from data; confidence is computed from checks.** They are separate
   axes and they gate different things — see §3–§4.
A bare "risk: 78" is a black box and a risk function would never accept it. A 78 that
decomposes into five visible bars is a defensible assessment.

---

## 1. The five signals

Each normalised to **0.0 – 1.0** per theme, each computed deterministically in
`core/signals.py`. No AI involved — these are arithmetic, reproducible, and auditable.

### `trend` — is this accelerating?

```
baseline = mean daily ticket count for this theme over days [-37, -8]
recent   = mean daily ticket count over the last 7 days
z        = (recent - baseline) / max(stdev(baseline_window), 0.5)
trend    = clip(z / 6, 0, 1)
```

The `max(..., 0.5)` floor stops a theme with a near-zero, near-constant baseline from
producing an infinite z-score — otherwise a single ticket on a dead theme scores 1.0.

### `novelty` — have we seen this before?

```
age_days = (today - theme.first_seen).days
novelty  = clip(1 - age_days / 30, 0, 1)
```

A theme first seen today scores 1.0; one that has been around 30+ days scores 0.0.
Deliberately separate from `trend`: an old theme can spike (trend high, novelty low) and
a brand-new theme can be flat (novelty high, trend low). Both are interesting, for
different reasons.

### `severity` — how bad is each ticket?

```
severity = (mean(t.severity_reported for t in theme) - 1) / 4
```

Straight rescale of the 1–5 reported severity onto 0–1.

### `recurrence` — has this happened before and come back?

```
episodes    = count of distinct activity bursts separated by ≥ 14 quiet days
recurrence  = clip((episodes - 1) / 2, 0, 1)
```

One episode → 0.0. Two → 0.5. Three or more → 1.0. This is the signal that makes the
APAC FX theme rank high despite its small size, and it is the one a risk analyst cares
about most: *a problem that keeps returning is a control failure, not an incident.*

### `blast_radius` — how far does it reach?

```
blast_radius = 0.5 * (distinct_regions / 4) + 0.5 * (distinct_systems / 7)
```

Split evenly between geographic and system spread. This is why S1's eBanking spillover
matters — a problem crossing two systems is structurally worse than the same volume
confined to one.

---

## 2. Risk score

```
risk_score = round(100 * (
    0.30 * trend
  + 0.20 * novelty
  + 0.25 * severity
  + 0.15 * recurrence
  + 0.10 * blast_radius
))
```

Weights live in one dict at the top of `core/score.py` and are **exposed as sliders in
the app sidebar**. Two reasons:

1. **Demo** — dragging a weight and watching the board re-rank live proves this is a real
   model, not a hardcoded list. Cheap to build, disproportionately convincing.
2. **Q&A** — "how did you pick those weights?" has a good answer: *we didn't, and we
   shouldn't. A risk function calibrates them to its own appetite. What we built is the
   instrument; the weights are a policy input.* That answer scores on Feasibility.

Expected demo ranking (Lane A verifies this at T+2:00):

| Theme | trend | nov | sev | rec | blast | **risk** |
|---|---|---|---|---|---|---|
| S1 mobile login | 0.94 | 0.92 | 0.55 | 0.0 | 0.64 | **~67** |
| S2 APAC FX | 0.45 | 0.0 | 0.75 | 1.0 | 0.32 | **~51** |
| S3 IBAN novel | 0.55 | 1.0 | 0.38 | 0.0 | 0.32 | **~49** |
| N1 password reset | 0.05 | 0.0 | 0.25 | 0.0 | 0.50 | **~13** |

The three planted themes must sit clearly above the background noise. If they don't after
real data lands, **tune the weights, don't fake the score** — and if a planted theme
genuinely doesn't score, that is Lane B's data to fix, not Lane A's formula to bend.

---

## 3. Confidence — derived, never self-reported

**Superseded by [GROUNDING.md §5](GROUNDING.md#5-confidence-is-derived-never-self-reported);
repeated here because it drives the gate below.**

A model that hallucinates a cause will happily report 0.9 next to it, so its own number is
advisory only — it can pull confidence *down*, never up:

```python
confidence = min(
    category_match_confidence,   # deterministic — match against the seed catalog
    grounding_score,             # deterministic — fraction of the model's claims verified
    llm_stated_confidence,       # advisory only
)
if state == "UNKNOWN":
    confidence = min(confidence, 0.30)   # hard ceiling — unseen never reaches automation
```

Two deterministic checks cap it, and an unseen case is capped below the automation
threshold by construction.

---

## 4. Triage gate — when does a human step in?

The obvious design ("auto-resolve anything above 80") is backwards: *high* risk is exactly
what you don't automate. Three axes, not one:

- **Risk** — how urgent is this?
- **Category state** — have we seen this class of problem before?
- **Confidence** — how safe is it to act without a human?

```
                       confidence (derived)
                    low              high
                 ┌──────────────┬────────────────┐
     high risk   │ HUMAN REVIEW │   ESCALATE     │
                 │              │ (now, with the │
                 │              │  evidence pack)│
                 ├──────────────┼────────────────┤
     low  risk   │ HUMAN REVIEW │  AUTO-RESOLVE  │
                 │              │  (playbook)    │
                 └──────────────┴────────────────┘

     state == UNKNOWN  →  HUMAN EXPERT, always. No cell of the matrix applies.
```

Implemented in `core/score.py`:

```python
HIGH_RISK = 45       # tuned against the demo data
HIGH_CONF = 0.75

if state == "UNKNOWN":
    action = "human_expert"      # never seen → a person decides, full stop
elif confidence < HIGH_CONF:
    action = "human_review"      # AI is unsure → a human decides
elif risk_score >= HIGH_RISK:
    action = "escalate"          # urgent + well-understood → route now, pre-briefed
elif playbook and playbook["auto_resolve_eligible"]:
    action = "auto_resolve"      # routine + well-understood → send the known fix
else:
    action = "human_review"      # no playbook exists → a human must decide
```

Four things worth saying out loud in the pitch:

- **Unseen always means a human.** This is the challenge author's requirement made
  structural: an UNKNOWN theme cannot reach the automated path, because its confidence is
  capped at 0.30 *and* the gate short-circuits before the matrix is consulted. Two
  independent mechanisms, deliberately.
- **Low confidence always routes to a human.** The system is allowed to say *"I don't
  know"* — the difference between decision support a bank can deploy and a chatbot it
  cannot.
- **Escalate is not "do nothing".** Tickets, timeline, correlated change, contributing
  factors — assembled before the human opens it. The AI does the 40 minutes of gathering;
  the human does the 2 minutes of judgement.
- **No playbook → human.** S3 has no playbook by design, so it routes to a person. Correct
  behaviour, and worth pointing at.

Every confirm/override is written to the audit log with the user, timestamp, action, and
whether it agreed with the recommendation. That becomes the calibration data for these
thresholds — the honest answer to *"how do you know the gate is set right?"* is
**you don't, at first; you measure it.**

---

## 5. Impact numbers (the closing tile)

All computed, none hardcoded — `core/evaluate.py`:

| Metric | How |
|---|---|
| Tickets → themes | `len(tickets)` → `len(themes)` |
| % auto-triaged | share of tickets in `auto_resolve` themes |
| Analyst hours saved / month | `Σ (tickets_auto_resolved × playbook.avg_resolution_minutes) / 60`, scaled to 30 days |
| Time-to-pattern | S1: hours between first ticket and the point the theme crosses the risk threshold, vs. a stated manual baseline of ~4 days |
| Cluster purity | against `_gt_theme` — the **only** place ground truth is read |
| LLM calls per run | count from the audit log — ~20 for 1,400 tickets, the scalability proof |
| Grounding rate | share of model claims verified against source data — should be 100% |
| Seen vs unseen | themes matched to a known category vs routed to a human expert |

**Be honest about the 4-day manual baseline** — it is our assumption, not a measurement.
Say "assumed" on the slide. Judges reward a clearly labelled assumption and punish a
number that turns out to be invented under questioning.
