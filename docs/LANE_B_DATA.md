# LANE B — Synthetic ticket data

**You own:** `gen/generate.py`, `data/tickets.json`, `data/changes.json`
**You must not edit:** anything in `core/`, `ai/`, `app.py`
**Read first:** [SCHEMA.md](SCHEMA.md) — the field contract is frozen there.

**Your deadline: a first complete `tickets.json` by T+0:50.** Rough is fine — Lane A
needs *something real* to tune clustering against. Polish the wording afterwards.

---

## Why this lane decides whether the demo lands

The whole demo is the story the data tells. If the planted storylines are weak, the
dashboard has nothing to find and every other lane's work is invisible. You are not
producing filler — you are writing the script the engine performs.

Three rules that matter more than volume:

1. **Plant the signal, don't plant the answer.** Only ~12% of tickets in a caused theme
   carry `linked_change_id`. The engine must find the cause by *timing*, not by reading
   a label. If everything is labelled, the judges see a lookup, not an insight.
2. **Decoys are as important as signals.** Innocent changes near the guilty ones,
   mundane themes around the interesting ones, genuine unclusterable singletons.
   A clean dataset proves nothing.
3. **Write like a human logged it.** Typos, partial sentences, "client called", second-hand
   phrasing from an advisor. LLM-perfect prose in every ticket looks synthetic on screen
   and makes TF-IDF unrealistically easy.

---

## Target composition (~1,400 tickets, 90 days ending 2026-09-22)

| # | Theme | Tickets | Shape | `_gt_theme` |
|---|---|---|---|---|
| **S1** | Mobile login failures after 4.2.0 | ~258 | sharp spike + decay | `mobile_login_failure_v42` |
| **S2** | APAC FX settlement mismatch | ~42 | 3 episodes of ~14 | `apac_fx_settlement_recurrence` |
| **S3** | Austrian IBAN validation rejects | ~11 | slow burn, low volume | `iban_validation_vendor_regression` |
| N1 | Password reset / locked account | ~230 | flat background | `password_reset` |
| N2 | Statement / document download fails | ~150 | flat, mild weekday peaks | `statement_download` |
| N3 | Card blocked while travelling | ~140 | flat, slight summer skew | `card_blocked_abroad` |
| N4 | Reporting slow at month-end | ~120 | 3 monthly bumps | `reporting_slow_month_end` |
| N5 | Onboarding document upload rejected | ~110 | flat | `onboarding_upload` |
| N6 | Payment beneficiary / limit queries | ~130 | flat | `payment_limits` |
| N7 | Branch / device / printer issues | ~95 | flat | `branch_hardware` |
| — | **Unclustered singletons** | ~115 (~8%) | random one-offs | `singleton` |

Volumes are targets, ±15% is fine. **S1 must be the largest single theme** and **S3 must
be the smallest** — that ordering is what the demo depends on.

---

## The three planted storylines — exact specs

### S1 — "Spike in login failures after a mobile update" *(the hero story)*

This is the one on screen for 60 of the 180 demo seconds. Get this one right first.

**The change:**
```json
{
  "change_id": "CHG-0042",
  "deployed_at": "2026-09-14T22:00:00Z",
  "system": "MobileApp",
  "title": "Mobile App 4.2.0 — migrate to new auth SDK",
  "type": "release",
  "regions": ["CH", "EMEA", "APAC", "AMER"],
  "owner_team": "Digital Channels",
  "rollback_at": null
}
```

**Volume curve** — baseline for MobileApp login tickets is ~2/day. Then:

| Day | Volume | Note |
|---|---|---|
| 2026-09-14 (deploy day) | 3 | deploy at 22:00 UTC, only a couple of late tickets |
| 2026-09-15 | 48 | **onset** — first tickets ~01:20 UTC (APAC morning) |
| 2026-09-16 | 62 | peak |
| 2026-09-17 | 54 | |
| 2026-09-18 | 38 | |
| 2026-09-19 | 26 | |
| 2026-09-20–21 | 12, 9 | weekend dip |
| 2026-09-22 (today) | 6 | still elevated, not resolved |

**Lag matters:** first tickets ~3h after deploy. Lane A's correlator scores lag — if the
spike starts *before* the deploy, the story breaks. Double-check this.

**Spillover:** ~18% of S1 tickets have `system: "eBanking"` — clients whose mobile login
fails go try the website. This is deliberate: it gives the theme a **blast radius across
two systems**, which is what makes the blast-radius signal non-trivial, and it is a
realistic detail a risk analyst will recognise.

**Attributes:** `severity_reported` mostly 3, some 4. `channel` heavy on `phone` and
`chat`. `reporter_role` mostly `client_advisor` and `client`. `region` all four,
roughly proportional to a retail client base (CH 35%, EMEA 30%, APAC 20%, AMER 15%).
`business_line` mostly `Retail`, some `Wealth`. ~12% carry `linked_change_id: "CHG-0042"`.

**Vocabulary** — vary these, mix and match, don't template one sentence:

> cannot log in · 2FA code not accepted · "Access Denied" after entering PIN ·
> app crashes on the login screen · biometric login stopped working · Face ID no longer
> offered · says session expired immediately · stuck on loading after PIN entry ·
> had to reinstall, still not working · works on the website but not the app

Example ticket bodies (write ~15 variants, sample with light random edits):

- *"Client called, since the app updated yesterday evening she gets 'Access Denied' after entering her PIN. Biometric also fails. Tried reinstalling, no change."*
- *"2FA push never arrives on the new app version. Client has been locked out since this morning. Escalating as she needs to authorise a payment today."*
- *"app just spins after i enter my pin. was fine before the update. iphone 15, ios 18.4"*
- *"Advisor reports 4 clients this morning with the same login problem on mobile. All updated the app in the last two days."*

### S2 — "Recurring FX issue in APAC"

**Three episodes**, each a 3-day cluster of ~14 tickets:

| Episode | Dates | Note |
|---|---|---|
| 1 | 2026-07-06 → 07-08 | |
| 2 | 2026-08-08 → 08-10 | |
| 3 | 2026-09-10 → 09-12 | most recent |

All `region: "APAC"`, `system: "FX-Trading"`, `business_line: "InvestmentBank"`,
`severity_reported` 4, `reporter_role` mostly `internal_ops` and `monitoring_bot`.

**The point of this theme is that it was "fixed" three times and keeps coming back.**
Make that visible in the data: each episode's tickets are `closed` with a
`resolution_notes` that is *near-identical across episodes*:

> *"Rates re-synced manually from the vendor feed and affected trades re-booked. Monitoring."*
> *"Manual re-sync of APAC rate feed, 6 trades re-booked. Closed."*

A risk analyst reading three identical closure notes three months running knows instantly
that nobody fixed the underlying problem. That is the insight the theme delivers.

**Vocabulary:**

> FX settlement mismatch · trade booked with stale rate · JPY/USD discrepancy at APAC close ·
> confirmation not received from counterparty · rate feed timestamp behind by ~40 minutes ·
> end-of-day reconciliation break on APAC book

Tie episode 3 loosely to a change (`CHG-0091`, a vendor market-data feed config change,
`type: "vendor"`) but **do not** tie episodes 1 and 2 to anything — that asymmetry is
realistic and lets the root-cause narrative say "correlates with the most recent vendor
change, but the pattern predates it."

### S3 — The novel slow-burn *(the "AI caught what rules missed" moment)*

**Underlying problem:** a new payments-vendor library rejects valid Austrian IBANs
(AT…) as malformed. 11 tickets, 2026-09-13 → 2026-09-22, 1–2 per day.

`system: "Payments"`, `severity_reported` 2–3, regions CH and EMEA, mixed channels.

**This one must be deliberately hard for TF-IDF.** Design constraint:

> **No single keyword appears in more than 4 of the 11 tickets.**

Describe the *same* problem 11 different ways — that is the whole trick. Some say IBAN,
some say account number, some say beneficiary, some describe the symptom without naming
the cause, some blame the client, one is a monitoring alert with a stack-trace-ish string.
Write these **by hand**, don't sample a template.

Examples:

- *"Client cannot add a new beneficiary in Austria, form says the account number is invalid. Checked it against her statement, it is correct."*
- *"Payment to AT61 1904 3002 3457 3201 rejected at entry, 'format not recognised'. Same payee worked in July."*
- *"Advisor: two Wealth clients this week unable to set up standing orders to Austrian banks."*
- *"validation error on beneficiary create, payload rejected upstream — VAL_IBAN_MALFORMED"*
- *"Transfer to Vienna account keeps bouncing back at the input screen. Client is frustrated, third attempt."*
- *"Cannot pay my Austrian supplier, the website says the IBAN is wrong but my bank confirmed it"*

Tie it to `CHG-0103` (`type: "vendor"`, `system: "Payments"`, deployed 2026-09-12,
*"Payments — upgrade beneficiary validation library to v3.1"*) but give **zero** tickets a
`linked_change_id`. Nobody connected the dots — that is precisely the point, and the
root-cause engine finding it anyway is the wow moment.

---

## Background themes (N1–N7)

Lower effort. ~6 phrasing templates each, light random variation, flat-ish daily volume
with weekday skew. What they need to be:

- **Plausible**, so the theme board looks like a real Monday
- **Distinct enough** to cluster cleanly — they are the 80% Stage 1 handles without AI
- **Not accidentally overlapping S1.** N1 (password reset) is the dangerous one: keep its
  language on *"forgot password"*, *"account locked after 3 attempts"*, *"reset link
  expired"* — and keep it off *"cannot log in"*, which belongs to S1. If N1 bleeds into
  S1 the hero theme gets muddy. This is the single most likely data bug; check it.

**Singletons (~115):** genuine one-offs. Statement address wrong, ATM ate a card,
complaint about fees, request to close an account, a duplicate ticket, a test ticket
someone filed by accident. These should *not* cluster — they prove the engine does not
force everything into a box, and they justify the "unclustered" count on screen.

---

## Changes file (~40 entries)

Three guilty: `CHG-0042` (S1), `CHG-0091` (S2 ep.3), `CHG-0103` (S3).

The other ~37 are decoys and must look exactly as plausible. Rules:

- Spread across all systems and all 90 days
- **Plant 1–2 innocent changes within ±48h of each guilty change**, ideally on a
  *different* system — this forces the correlator to discriminate on system and region,
  not just time. E.g. an `eBanking` config change on 2026-09-15 at 06:00, a
  `CardServices` release on 2026-09-13.
- Mix of types: ~50% `release`, 20% `config`, 15% `infra`, 10% `vendor`, 5% `certificate`
- A couple with a non-null `rollback_at` — realistic texture

Titles should read like a real change calendar: *"eBanking — quarterly dependency patch"*,
*"Payments — increase SEPA batch window"*, *"Infra — failover test, Zurich DC"*.

---

## Getting started

```bash
mkdir -p gen data
```

Skeleton to build on — `gen/generate.py`:

```python
"""Synthetic ticket generator for TRACE. See docs/LANE_B_DATA.md."""
import json, random
from datetime import datetime, timedelta, timezone

random.seed(42)                      # deterministic — the demo must be reproducible

END   = datetime(2026, 9, 22, tzinfo=timezone.utc)
START = END - timedelta(days=90)

TZ_OFFSET = {"CH": 2, "EMEA": 2, "APAC": 8, "AMER": -5}

_counter = 0
def next_id() -> str:
    global _counter
    _counter += 1
    return f"INC-{_counter:07d}"

def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def business_hours_ts(day: datetime, region: str) -> datetime:
    """Pick a plausible local-business-hours time, returned in UTC."""
    local_hour = random.choices(
        population=list(range(6, 21)),
        weights=[1, 3, 6, 9, 10, 9, 7, 8, 9, 8, 6, 4, 3, 2, 1],
    )[0]
    return day.replace(
        hour=0, minute=0, second=0, microsecond=0
    ) + timedelta(hours=local_hour - TZ_OFFSET[region], minutes=random.randint(0, 59))

def make_ticket(day, *, theme, system, region, business_line, severity,
                channel, reporter_role, title, description,
                status="open", resolution_notes=None, linked_change_id=None):
    return {
        "ticket_id": next_id(),
        "created_at": iso(business_hours_ts(day, region)),
        "channel": channel,
        "region": region,
        "business_line": business_line,
        "system": system,
        "title": title,
        "description": description,
        "reporter_role": reporter_role,
        "severity_reported": severity,
        "status": status,
        "resolution_notes": resolution_notes,
        "linked_change_id": linked_change_id,
        "_gt_theme": theme,
    }

# --- storylines -------------------------------------------------------------
def gen_s1_mobile_login(): ...   # the spike — see the volume curve in the doc
def gen_s2_apac_fx():      ...   # three episodes
def gen_s3_iban():         ...   # 11 hand-written tickets
def gen_background():      ...   # N1..N7
def gen_singletons():      ...
def gen_changes():         ...   # 3 guilty + ~37 decoys

if __name__ == "__main__":
    tickets = (gen_s1_mobile_login() + gen_s2_apac_fx() + gen_s3_iban()
               + gen_background() + gen_singletons())
    tickets.sort(key=lambda t: t["created_at"])
    json.dump(tickets, open("data/tickets.json", "w"), indent=1, ensure_ascii=False)
    json.dump(gen_changes(), open("data/changes.json", "w"), indent=1, ensure_ascii=False)
    print(f"{len(tickets)} tickets written")
```

`random.seed(42)` is not optional. If the data changes shape between your last run and
the demo, Lane A's score tuning is invalidated and the themes may re-rank on stage.
**Once Lane A confirms the themes rank correctly, stop regenerating.**

---

## Every time you hand over new data

```bash
python gen/generate.py
python -m core.schema data/tickets.json     # must print 0 errors
python -m core.schema data/changes.json
```

Then tell the group: **"tickets.json updated — N tickets"**, so Lane A knows to re-run and
re-check that the themes still rank correctly. Silent data changes are how a demo breaks
ten minutes before it starts.

---

## Definition of done

- [ ] `python -m core.schema` reports 0 errors on both files
- [ ] ~1,400 tickets, 90 days, every enum value legal
- [ ] S1 spike starts **after** `CHG-0042`'s `deployed_at`, first tickets ~3h later
- [ ] S1 is the largest theme; S3 is the smallest
- [ ] S1 spans two systems (MobileApp + eBanking spillover)
- [ ] S2 has exactly 3 episodes with near-identical resolution notes
- [ ] S3: no keyword in more than 4 of its 11 tickets; no `linked_change_id` on any
- [ ] N1 (password reset) does **not** use the phrase "cannot log in"
- [ ] ~12% `linked_change_id` coverage in S1, not 100%
- [ ] ≥1 innocent change within ±48h of each guilty change
- [ ] Reading 10 random tickets out loud, they sound like a human wrote them
