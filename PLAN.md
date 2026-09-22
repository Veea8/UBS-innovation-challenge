# TRACE — Ticket Risk & Cause Engine

**UBS Hackathon · Scenario 1 — Ticket Intelligence and Theme Detection**

> From noise to insight: helping risk teams understand what's really going wrong.

---

## 1. What we are building

A Streamlit dashboard for a **risk / operations analyst**. It takes a raw stream of
incident tickets and produces:

1. **Themes** — tickets grouped into meaningful clusters
2. **Patterns** — which themes are spiking, recurring, or brand new
3. **Root causes** — evidence-linked hypotheses (correlated against a change/deployment log)
4. **Actions** — a confidence-gated recommendation, with a human confirmation step

Every conclusion is traceable back to the tickets and the AI calls that produced it.

---

## 2. The core design decision (say this in Q&A)

**Two-stage routing.** We do *not* throw an LLM at every ticket.

| Stage | What it does | Cost | Deterministic? |
|---|---|---|---|
| **Stage 1** | TF-IDF + agglomerative clustering groups the bulk of tickets | ~free | Yes, reproducible |
| **Stage 2** | Apertus names themes, writes root-cause narratives, and classifies the leftovers Stage 1 could not place | ~20 calls per run | No, but fully logged |

Why this matters to the judges:

- **Technology Innovation** — AI is used where it adds value (language, reasoning,
  novelty detection), not as a sledgehammer.
- **Feasibility & Scalability** — cost scales with *themes*, not with *ticket volume*.
  100k tickets/month still costs ~20 LLM calls per run.
- **Transparency** — the deterministic stage is auditable by construction; the AI stage
  is auditable because every prompt and response is logged and replayable.

**Apertus** (Swiss open LLM) is the model. For UBS this is a sovereignty story:
the model can be hosted in Switzerland, no ticket text leaves the bank's control.

---

## 3. Pipeline

```
data/tickets.json ─┐
data/changes.json ─┼─→ [1] ingest + validate      (core/schema.py)
data/playbooks.json┘
                      ↓
                   [2] Stage 1 clustering          (core/cluster.py)
                       TF-IDF → agglomerative → themes + leftovers
                      ↓
                   [3] Stage 2 Apertus             (ai/apertus.py)
                       name_theme() · classify_novel()
                      ↓
                   [4] signals per theme           (core/signals.py)
                       trend · novelty · severity · recurrence · blast radius
                      ↓
                   [5] risk score + triage gate    (core/score.py)
                      ↓
                   [6] root cause correlation      (core/rootcause.py)
                       time-correlate against changes.json → Apertus narrative
                      ↓
                   [7] audit log                   (core/audit.py)
                      ↓
                   app.py  (Streamlit)
```

See [`docs/SCORING.md`](docs/SCORING.md) for the exact formulas.

---

## 4. Lanes — who owns what

Each lane owns its files exclusively. **Don't edit files outside your lane** — if you need
something changed there, say so in the group chat. That one rule is what stops four people
from stepping on each other.

| Lane | Owner | Owns these files | Brief |
|---|---|---|---|
| **A — Pipeline + app** | Jonas / Claude | `core/*.py`, `app.py`, `docs/*` | [LANE_A_PIPELINE.md](docs/LANE_A_PIPELINE.md) |
| **B — Synthetic data** | teammate 1 | `gen/generate.py`, `data/tickets.json`, `data/changes.json` | [LANE_B_DATA.md](docs/LANE_B_DATA.md) |
| **C — Apertus** | teammate 2 | `ai/apertus.py`, `ai/prompts.py`, `data/cache/llm_cache.json` | [LANE_C_APERTUS.md](docs/LANE_C_APERTUS.md) |
| **D — Playbooks + pitch** | teammate 3 | `data/playbooks.json`, `slides/`, `docs/DEMO_SCRIPT.md` | [LANE_D_PITCH.md](docs/LANE_D_PITCH.md) |

The contracts that hold it together: **[docs/SCHEMA.md](docs/SCHEMA.md)**. Read it first.
It is frozen — if it must change, it changes in the group chat, not in a commit.

Lane A writes runnable stubs for every module in the first 20 minutes, so nobody is
blocked waiting for anybody else. Stubs return realistic fake objects that satisfy the
schema, so the app runs end-to-end from minute 20 and gets *more real* as each lane
replaces its stub.

**Your lane doc is your task list.** Each one ends with a "Definition of done" checklist —
that is the whole of what you owe the team. Work through it top to bottom; the items are
already in the right order.

---

## 5. Timeline (3 hours)

| Time | Milestone |
|---|---|
| **0:00 – 0:20** | Lane A: scaffold + stubs ready. Everyone else: read your lane doc, `pip install -r requirements.txt`, confirm the app runs. |
| **0:20 – 1:30** | Parallel build. B produces a first `tickets.json` by **0:50** even if rough — A needs it to tune clustering. C gets one Apertus call working by **0:50**. |
| **1:30 – 2:00** | **Integration 1.** Real data + real Apertus in the app. Expect breakage here; budget for it. |
| **2:00 – 2:30** | Tune the risk score so the demo themes rank correctly. Polish UI. D drafts slides against the *actual* screen. |
| **2:30 – 2:45** | **FREEZE.** Snapshot every Apertus response into `data/cache/llm_cache.json`, switch demo to `APERTUS_MODE=cache_only`. No code changes after this except crash fixes. |
| **2:45 – 3:00** | Two full dry runs against a timer. |

**Hard rule:** the demo must never depend on live network. Cache everything at 2:30.

---

## 6. The 3-minute demo

Full script in [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md). Shape:

| Sec | Beat |
|---|---|
| 0–20 | The raw table. 1,400 tickets, 90 days, unreadable. "This is a Monday morning." |
| 20–40 | One click → 8 ranked themes. Noise collapses into a board. |
| 40–75 | Open the red theme: timeline with the spike, deploy marker 3h before onset. |
| 75–105 | Risk score breakdown bar + root cause + contributing factors + evidence tickets. |
| 105–135 | "This recurred twice before" → the APAC FX theme, three episodes, same fix each time. |
| 135–155 | The novel theme Stage 1 missed and Apertus caught. 11 tickets, no shared keyword. |
| 155–170 | Triage matrix → human confirms → decision logged. AI audit log tab. |
| 170–180 | Impact tile: 1,400 → 8. 62% auto-triaged. Time-to-pattern 4 days → 6 minutes. |

---

## 7. What is mocked (we must declare this)

Kept current in [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md#what-is-mocked). Honest list:

- **Ticket and change data is synthetic**, generated by `gen/generate.py` with planted
  storylines. No real UBS data.
- **Playbook links** point nowhere — they stand in for an internal KB.
- **No ServiceNow/Jira connector** — ingestion reads JSON files. The adapter is one
  function; the schema is the contract.
- Everything else — clustering, signals, scoring, triage, Apertus calls, audit log — is real.

Saying this plainly *gains* points on Feasibility. Do not bury it.

---

## 8. Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add Apertus key
streamlit run app.py
```

Environment variables — see [docs/LANE_C_APERTUS.md](docs/LANE_C_APERTUS.md#configuration).

---

## 9. Open items

- [ ] Apertus endpoint + key + model name → blocks Lane C only
- [ ] Confirm product name (TRACE) — trivial to change, it is one constant in `app.py`
- [ ] Agree how files get shared between the four of us (same machine / repo / chat)
