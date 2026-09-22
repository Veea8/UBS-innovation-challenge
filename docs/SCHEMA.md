# SCHEMA — the frozen contracts

**Everyone reads this first.** Every lane codes against these shapes. If a field has to
change, it changes by agreement in the group chat and this file is updated in the same
minute — never silently in code.

All timestamps are **ISO 8601 UTC with a `Z` suffix**: `2026-09-15T08:13:00Z`.
All files are **UTF-8 JSON**, top-level array unless stated otherwise.

---

## 1. Ticket — `data/tickets.json`

Owner: **Lane B**. Consumed by: A (everything), D (screenshots).

```json
{
  "ticket_id": "INC-0001234",
  "created_at": "2026-09-15T08:13:00Z",
  "channel": "phone",
  "region": "EMEA",
  "business_line": "Retail",
  "system": "MobileApp",
  "title": "Cannot log in to mobile app after update",
  "description": "Client called: since updating the app yesterday evening she gets 'Access Denied' after entering her PIN. Biometric login also fails. Tried reinstalling, no change.",
  "reporter_role": "client_advisor",
  "severity_reported": 3,
  "status": "open",
  "resolution_notes": null,
  "linked_change_id": null,
  "_gt_theme": "mobile_login_failure_v42"
}
```

| Field | Type | Allowed values / rules |
|---|---|---|
| `ticket_id` | string | `INC-` + 7 digits, zero-padded, unique |
| `created_at` | string | ISO 8601 UTC |
| `channel` | enum | `phone` `email` `chat` `monitoring` `branch` |
| `region` | enum | `CH` `EMEA` `APAC` `AMER` |
| `business_line` | enum | `Retail` `Wealth` `InvestmentBank` `Operations` |
| `system` | enum | `eBanking` `MobileApp` `FX-Trading` `Payments` `CardServices` `Onboarding` `Reporting` |
| `title` | string | 4–12 words, no trailing period |
| `description` | string | 1–4 sentences, natural human phrasing, 120–400 chars |
| `reporter_role` | enum | `client` `client_advisor` `internal_ops` `monitoring_bot` |
| `severity_reported` | int | `1`–`5`, **5 = most severe** |
| `status` | enum | `open` `in_progress` `resolved` `closed` |
| `resolution_notes` | string \| null | non-null **only** when status is `resolved` or `closed` |
| `linked_change_id` | string \| null | must match a `change_id` in `changes.json`, or null |
| `_gt_theme` | string | ground-truth label — see below |

### The `_` prefix rule

Any field starting with `_` is **ground truth for evaluation only**.

- The pipeline **must not read it** — not in clustering, signals, scoring or prompts.
- Only `core/evaluate.py` may read it, to compute cluster purity for the impact tile.
- Lane A enforces this: the loader strips `_*` fields into a separate dict before the
  pipeline ever sees a ticket.

This lets us show a real, measurable number on stage: *"we recovered 7 of the 8 planted
themes, 0.91 purity"* — instead of asking the judges to take clustering quality on faith.

### Volume and shape

- **~1,400 tickets** spanning **90 days**, ending **today (2026-09-22)**.
- Weekday-heavy: weekends at ~25% of weekday volume.
- Business-hours skew **in the ticket's own region's timezone** (CH/EMEA → UTC+2,
  APAC → UTC+8, AMER → UTC-5). A flat UTC distribution looks fake on the timeline.
- ~60% `closed`/`resolved`, ~30% `open`, ~10% `in_progress`. Older tickets skew closed.
- **~12%** of tickets in a change-caused theme carry `linked_change_id`. Not 100% —
  if every ticket named its cause, root-cause detection would be trivial and the demo
  would be hollow. The engine must work on **timing**, with the linked minority as
  corroborating evidence.

---

## 2. Change — `data/changes.json`

Owner: **Lane B**. Consumed by: A (`core/rootcause.py`).

The deployment / change log. This is what makes root cause *evidence-linked* rather than
LLM guesswork.

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

| Field | Type | Rules |
|---|---|---|
| `change_id` | string | `CHG-` + 4 digits, unique |
| `deployed_at` | string | ISO 8601 UTC |
| `system` | enum | same enum as ticket `system` |
| `title` | string | reads like a real change record |
| `type` | enum | `release` `config` `infra` `vendor` `certificate` |
| `regions` | array | subset of the region enum, non-empty |
| `owner_team` | string | free text, e.g. `Digital Channels`, `Payments Engineering` |
| `rollback_at` | string \| null | ISO 8601 or null |

**~40 changes** over the 90 days. Most are innocent — they are the decoys. If only the
three guilty changes exist, correlation is meaningless. In particular, plant **1–2
innocent changes within ±48h of each guilty one** so the correlation has to actually
discriminate on system, region and lag.

---

## 3. Playbook — `data/playbooks.json`

Owner: **Lane D**. Consumed by: A (`core/score.py` triage gate).

```json
{
  "playbook_id": "PB-LOGIN-001",
  "title": "Authentication failure after client app update",
  "match_systems": ["MobileApp", "eBanking"],
  "match_keywords": ["login", "log in", "authentication", "2fa", "access denied", "biometric"],
  "resolution_steps": [
    "Confirm the client is on app version 4.2.0 or later",
    "Have the client clear the app's stored credentials (Settings → Security → Reset)",
    "Re-enrol biometric login",
    "If still failing, raise to Digital Channels with the device model and OS version"
  ],
  "self_service_link": "https://intranet.ubs.example/kb/auth-after-update",
  "avg_resolution_minutes": 25,
  "auto_resolve_eligible": true
}
```

| Field | Type | Rules |
|---|---|---|
| `playbook_id` | string | `PB-` + short slug + 3 digits |
| `title` | string | what the playbook fixes |
| `match_systems` | array | subset of the system enum |
| `match_keywords` | array | lowercase; matched against title + description |
| `resolution_steps` | array | 3–6 imperative steps |
| `self_service_link` | string | **mocked**, `*.example` domain so nobody thinks it is real |
| `avg_resolution_minutes` | int | feeds the "time saved" impact tile |
| `auto_resolve_eligible` | bool | false for anything a human must always see |

**8–10 playbooks.** Must cover the mundane background themes (password reset, statement
download, card blocked abroad) plus the login theme. Deliberately **no playbook** for the
novel IBAN theme — "no playbook exists for this" is exactly why it routes to a human.

---

## 4. Theme — produced by Lane A, in memory

Not a file you write, but the shape the app renders. Documented so Lane D can design
slides against it and Lane C knows what its output feeds.

```json
{
  "theme_id": "T-03",
  "name": "Mobile login failures after 4.2.0 auth SDK migration",
  "summary": "Clients on MobileApp 4.2.0 cannot authenticate; PIN and biometric both rejected. Spillover to eBanking as clients retry on web.",
  "ticket_ids": ["INC-0001234", "..."],
  "size": 258,
  "stage1_keywords": ["login", "access denied", "2fa", "biometric"],
  "first_seen": "2026-09-15T01:20:00Z",
  "last_seen": "2026-09-22T09:40:00Z",
  "signals": {
    "trend": 0.94, "novelty": 0.92, "severity": 0.55,
    "recurrence": 0.0, "blast_radius": 0.64
  },
  "risk_score": 78,
  "root_cause": {
    "hypothesis": "...",
    "contributing_factors": ["...", "..."],
    "confidence": 0.81,
    "evidence": [
      {"kind": "change_correlation", "change_id": "CHG-0042", "lag_hours": 3.2, "detail": "..."},
      {"kind": "linked_tickets", "count": 31, "detail": "..."},
      {"kind": "ticket_quote", "ticket_id": "INC-0001234", "detail": "..."}
    ]
  },
  "triage": {
    "action": "escalate",
    "confidence": 0.81,
    "playbook_id": "PB-LOGIN-001",
    "rationale": "High risk (78) with high confidence — route to a human now with the evidence pack pre-built."
  },
  "provenance": {
    "stage": "deterministic",
    "ai_calls": ["call_7f3a", "call_9b21"]
  }
}
```

`signals` values are all normalised **0.0–1.0**. `risk_score` is an **int 0–100**.
`triage.action` is one of `auto_resolve` `human_review` `escalate`.
`provenance.stage` is `deterministic` (Stage 1 found it) or `ai` (Stage 2 found it) —
the app badges these differently, and the `ai` badge is the money shot for the novel theme.

---

## 5. Audit entry — `core/audit.py`, rendered in the AI Audit tab

Every Apertus call produces one of these. Nothing the AI says reaches the screen without
one.

```json
{
  "call_id": "call_7f3a",
  "ts": "2026-09-22T14:03:11Z",
  "function": "name_theme",
  "theme_id": "T-03",
  "model": "apertus-70b-instruct",
  "source": "live",
  "prompt": "<full prompt text>",
  "response": "<full raw response text>",
  "parsed": { "...": "..." },
  "latency_ms": 1840
}
```

`source` is `live` or `cache`. During the demo everything will read `cache` — that is
fine and honest; the tab shows the prompt and the response either way.

---

## 6. File layout

```
UBS-innovation-challenge/
├── PLAN.md
├── README.md
├── requirements.txt
├── .env.example
├── app.py                     # Lane A
├── core/                      # Lane A
│   ├── schema.py              #   load + validate + strip _gt_* fields
│   ├── cluster.py             #   Stage 1
│   ├── signals.py             #   trend/novelty/severity/recurrence/blast
│   ├── score.py               #   risk score + triage gate
│   ├── rootcause.py           #   change correlation
│   ├── evaluate.py            #   the ONLY module allowed to read _gt_*
│   └── audit.py               #   AI decision log
├── ai/                        # Lane C
│   ├── apertus.py             #   client + cache + the three functions
│   └── prompts.py             #   prompt templates
├── gen/                       # Lane B
│   └── generate.py
├── data/
│   ├── tickets.json           # Lane B  (generated, committed)
│   ├── changes.json           # Lane B  (generated, committed)
│   ├── playbooks.json         # Lane D  (hand-written)
│   └── cache/
│       └── llm_cache.json     # Lane C  (generated, committed at freeze)
├── slides/                    # Lane D
└── docs/
    ├── SCHEMA.md              # this file
    ├── SCORING.md
    ├── LANE_A_PIPELINE.md
    ├── LANE_B_DATA.md
    ├── LANE_C_APERTUS.md
    ├── LANE_D_PITCH.md
    └── DEMO_SCRIPT.md
```

---

## 7. Validation

Lane A ships `core/schema.py` with:

```python
validate_tickets(path) -> tuple[list[dict], list[str]]   # (tickets, errors)
validate_changes(path) -> tuple[list[dict], list[str]]
validate_playbooks(path) -> tuple[list[dict], list[str]]
```

and a CLI so Lanes B and D can self-check without running the app:

```bash
python -m core.schema data/tickets.json
# ✓ 1412 tickets, 0 errors
# ✓ 8 ground-truth themes present
```

**Run it before every commit of a data file.** A schema break found at integration time
costs the whole team 15 minutes we do not have.
