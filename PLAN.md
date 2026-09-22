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

## 2. The two core design decisions (say these in Q&A)

### 2a. Two-stage routing — AI where it earns its cost

We do *not* throw an LLM at every ticket.

| Stage | What it does | Cost | Deterministic? |
|---|---|---|---|
| **Stage 1** | TF-IDF + agglomerative clustering groups the bulk of tickets; deterministic matching against a seed category catalog | ~free | Yes, reproducible |
| **Stage 2** | LLM names themes, writes root-cause narratives, and classifies the leftovers Stage 1 could not place | ~20 calls per run | No, but fully logged and verified |

Why this matters to the judges:

- **Technology Innovation** — AI is used where it adds value (language, reasoning,
  novelty detection), not as a sledgehammer.
- **Feasibility & Scalability** — cost scales with *themes*, not with *ticket volume*.
  100k tickets/month still costs ~20 LLM calls per run.
- **Transparency** — the deterministic stage is auditable by construction; the AI stage
  is auditable because every prompt and response is logged and replayable.

**Model:** provider-agnostic, OpenAI or Gemini behind one interface (`LLM_PROVIDER`).
Switching is one environment variable and zero code changes. Apertus was dropped — the
challenge author had no preference, so we optimise for reliability on the day.

### 2b. Grounded by construction — and honest about what it hasn't seen

Straight from the challenge author, and now the spine of the system:

> **The AI must not hallucinate — a decision must not interact with external data.
> Seen cases get high confidence; unseen cases go to a human expert.**

Four structural controls, none of them merely a prompt instruction:

1. **Closed world.** The model gets a CONTEXT block built only from our tickets, changes
   and category catalog. No tools, no web, no retrieval, no appeal to its own world
   knowledge.
2. **Post-hoc verification.** `core/grounding.py` checks every ticket id, change id,
   system, region, date and quote the model produced against the context it was given.
   Unverified claims are struck through on screen; badly grounded output is suppressed
   entirely and the theme falls back to a deterministic summary.
3. **Seed categories.** `data/categories.json` holds the known-problem catalog. Matching
   is deterministic. A theme is **KNOWN**, **KNOWN-VARIANT** or **UNKNOWN** — and on
   UNKNOWN the model is not permitted to state a cause at all, only to describe what the
   tickets have in common.
4. **Derived confidence.** The model's self-reported confidence is advisory and can only
   *lower* the score, never raise it. Two deterministic checks cap it, and UNKNOWN is
   hard-capped below the automation threshold.

The line to use: **"the model cannot talk its way into being trusted"** — and it is
literally true of the code.

Full specification in **[docs/GROUNDING.md](docs/GROUNDING.md)**. Read it before writing
any prompt or any rendering code.

---

## 3. Pipeline

```
data/tickets.json  ─┐
data/changes.json  ─┤
data/playbooks.json─┼─→ [1] ingest + validate      (core/schema.py)
data/categories.json┘      strips _gt_* ground truth
                      ↓
                   [2] Stage 1 clustering          (core/cluster.py)
                       TF-IDF → agglomerative → themes + leftovers
                      ↓
                   [3] category match              (core/categories.py)
                       deterministic → KNOWN / KNOWN-VARIANT / UNKNOWN
                      ↓
                   [4] root cause correlation      (core/rootcause.py)
                       time-correlate against changes.json → ranked shortlist
                      ↓
                   [5] Stage 2 LLM                 (ai/llm.py)
                       name_theme · explain_root_cause · classify_novel
                       closed-world CONTEXT block only
                      ↓
                   [6] grounding validation        (core/grounding.py)
                       verify every entity the model named
                      ↓
                   [7] signals per theme           (core/signals.py)
                       trend · novelty · severity · recurrence · blast radius
                      ↓
                   [8] risk score + triage gate    (core/score.py)
                       confidence = min(category, grounding, llm)
                      ↓
                   [9] audit log                   (core/audit.py)
                      ↓
                   app.py  (Streamlit)
```

Note the ordering: **correlation happens before the model call.** The LLM never
searches for a cause; it assesses a shortlist we computed deterministically.

Formulas in [`docs/SCORING.md`](docs/SCORING.md); grounding rules in
[`docs/GROUNDING.md`](docs/GROUNDING.md).

---

## 4. Lanes — who owns what

Each lane owns its files exclusively. **Don't edit files outside your lane** — if you need
something changed there, say so in the group chat. That one rule is what stops four people
from stepping on each other.

| Lane | Owner | Owns these files | Brief |
|---|---|---|---|
| **A — Pipeline + app** | Jonas / Claude | `core/*.py`, `app.py`, `docs/*` | [LANE_A_PIPELINE.md](docs/LANE_A_PIPELINE.md) |
| **B — Synthetic data** | teammate 1 | `gen/generate.py`, `data/tickets.json`, `data/changes.json` | [LANE_B_DATA.md](docs/LANE_B_DATA.md) |
| **C — LLM** | teammate 2 | `ai/llm.py`, `ai/prompts.py`, `data/cache/llm_cache.json` | [LANE_C_LLM.md](docs/LANE_C_LLM.md) |
| **D — Categories, playbooks + pitch** | teammate 3 | `data/categories.json`, `data/playbooks.json`, `slides/`, `docs/DEMO_SCRIPT.md` | [LANE_D_PITCH.md](docs/LANE_D_PITCH.md) |

The contracts that hold it together: **[docs/SCHEMA.md](docs/SCHEMA.md)** and
**[docs/GROUNDING.md](docs/GROUNDING.md)**. Read both first. They are frozen — if
something must change, it changes by agreement in the group chat, never silently.

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
| **0:20 – 1:30** | Parallel build. B produces a first `tickets.json` by **0:50** even if rough — A needs it to tune clustering. C gets one real LLM call returning parsed JSON by **0:50**. |
| **1:30 – 2:00** | **Integration 1.** Real data + real LLM in the app. Expect breakage here; budget for it. |
| **2:00 – 2:30** | Tune the risk score so the demo themes rank correctly. Polish UI. D drafts slides against the *actual* screen. |
| **2:30 – 2:45** | **FREEZE.** Snapshot every LLM response into `data/cache/llm_cache.json`, switch demo to `LLM_MODE=cache_only`. No code changes after this except crash fixes. |
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
| 135–155 | The **UNKNOWN** theme Stage 1 missed and the LLM caught. 11 tickets, no shared keyword, and the system refuses to guess a cause. |
| 155–170 | Triage matrix → human confirms → decision logged. Audit tab: prompt, response, grounding check. |
| 170–180 | Impact tile: 1,400 → 8. 62% auto-triaged. Time-to-pattern 4 days → 6 minutes. |

---

## 7. What is mocked (we must declare this)

Kept current in [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md#what-is-mocked). Honest list:

- **Ticket and change data is synthetic**, generated by `gen/generate.py` with planted
  storylines. No real UBS data.
- **Playbook links** point nowhere — they stand in for an internal KB.
- **No ServiceNow/Jira connector** — ingestion reads JSON files. The adapter is one
  function; the schema is the contract.
- Everything else — clustering, category matching, signals, scoring, triage, LLM calls,
  grounding validation, audit log — is real.

Saying this plainly *gains* points on Feasibility. Do not bury it.

---

## 8. Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add OpenAI or Gemini key
streamlit run app.py
```

Environment variables — see [docs/LANE_C_LLM.md](docs/LANE_C_LLM.md#configuration).

---

## 9. Open items

- [ ] OpenAI or Gemini API key → Lane C works against the `mock` provider until it lands
- [ ] Confirm product name (TRACE) — trivial to change, it is one constant in `app.py`
- [ ] Agree how files get shared between the four of us (same machine / repo / chat)
