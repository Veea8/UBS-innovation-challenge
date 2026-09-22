# LANE A — Pipeline + Streamlit app

**Owner:** Jonas / Claude
**Owns:** `core/*.py`, `app.py`, `requirements.txt`, `docs/*`
**Published here so the other three lanes know what is coming and when.**

Everything in [GROUNDING.md](GROUNDING.md) is binding on this lane — it is where the
closed-world contract and the confidence derivation are actually enforced.

---

## Obligation to the other lanes

By **T+0:20** every module below exists and runs with stub data, so nobody waits:

- `core/schema.py` works for real immediately — Lanes B and D need the validator CLI
- `ai/llm.py` ships as a `mock`-provider stub returning plausible fixed strings; Lane C replaces it
- `data/tickets.json` ships as a 50-ticket hand-made sample; Lane B replaces it
- `data/playbooks.json` and `data/categories.json` ship with 2–3 examples each; Lane D replaces them

`streamlit run app.py` renders a full dashboard from minute 20. It just gets more real
as each lane lands.

---

## Modules

### `core/schema.py`
Load, validate, and **strip `_`-prefixed ground-truth fields** before anything downstream
sees a ticket. Returns `(clean_tickets, ground_truth_map, errors)`. Exposes the CLI
Lanes B and D use:

```bash
python -m core.schema data/tickets.json
```

The stripping is structural, not a convention — it means no prompt and no clustering
feature can accidentally see the answer, and we can say that honestly on stage.

### `core/cluster.py` — Stage 1
TF-IDF over `title + description` (English stop words, 1–2 grams, `min_df=3`), cosine
distance, agglomerative clustering with a distance threshold. Clusters below a minimum
size (3) are released as **leftovers** for Stage 2.

Also extracts each cluster's top discriminative terms → `stage1_keywords`, which feed
both the UI chips and the `name_theme` prompt context.

Why not embeddings: no dependency on an embedding endpoint or API key we may not have,
no model download on conference wifi, runs in under a second, and — the real reason —
it is **deterministic and explainable**, which is the whole thesis of Stage 1. If time
allows at T+2:00, `sentence-transformers` is a drop-in behind the same interface.

### `core/signals.py`
The five signals from [SCORING.md](SCORING.md). Pure functions over a theme's tickets.

### `core/score.py`
Weighted risk score + the triage gate. Weights in one module-level dict, surfaced as
sidebar sliders.

### `core/categories.py`
Deterministic match of each theme against `data/categories.json` → `match_score` and a
state of `KNOWN` / `KNOWN-VARIANT` / `UNKNOWN`. No model involved: whether we have seen
something before is a fact about our catalog, not a judgement call. Formula in
[GROUNDING.md §3](GROUNDING.md#3-known-categories--datacategoriesjson).

### `core/grounding.py`
Post-hoc verification of every model response. Extracts every ticket id, change id,
system, region, date and quoted string the model produced and checks each against the
context that was sent (recovered from `_raw["user"]`). Returns
`{grounded, score, verified, unverified}`. Unverified claims render struck through;
`score < 0.5` suppresses the narrative entirely and falls back to the deterministic
summary. Rules in [GROUNDING.md §2](GROUNDING.md#2-the-grounding-validator--coregroundingpy).

This module is the difference between claiming the system doesn't hallucinate and
demonstrating it. Build it before polishing anything visual.

### `core/rootcause.py`
Time-correlation, run **before** the LLM so the model reasons over evidence rather than
searching:

1. Detect theme **onset** — first day the daily count exceeds `baseline + 2σ`
2. Find every change in the window `[onset - 72h, onset]`
3. Score each candidate: lag (closer = better, with a floor — a change *after* onset is
   disqualified), system match, region overlap, count of tickets carrying its `change_id`
4. Hand the top 3 to `explain_root_cause()` — and nothing else, so a cause outside this
   shortlist cannot survive the grounding check

The disqualification rule matters: a cause cannot postdate its effect, and saying that
out loud in Q&A shows the correlation isn't naive.

### `core/evaluate.py`
The only module permitted to read ground truth. Cluster purity, themes recovered, and the
impact tile numbers.

### `core/audit.py`
Append-only log of every AI call (from `_raw`) and every human confirm/override. Rendered
in the **AI Audit** tab and exportable to JSON — "here is the evidence pack for the
regulator" is a good closing line.

---

## App layout

**Sidebar** — data source, date range, risk weight sliders, provider + `LLM_MODE` badge
(`openai`/`gemini`/`mock` · `live`/`cache`), "Re-run pipeline" button.

**Tab 1 · Raw** — the 1,400-row table. Deliberately overwhelming. This is the "before".

**Tab 2 · Themes** — ranked cards: name, risk score, sparkline, size, badges
(`NEW` / `RECURRING` / `AI-DETECTED` / `UNSEEN`), triage action chip. This is the "after", and the
cut between tabs 1 and 2 is the single most important transition in the demo.

**Tab 3 · Theme detail** — the centrepiece:
- a state badge: **KNOWN** / **KNOWN-VARIANT** / **UNKNOWN**, and a **✓ grounded** badge
- timeline with the spike **and a vertical deploy marker** for the correlated change
- risk score as a stacked component bar, not a number
- root-cause hypothesis + contributing factors + evidence list (icon per `evidence.kind`)
- the actual evidence tickets, expandable
- recurrence strip if `episodes > 1`
- recommended action + **Confirm / Override** buttons → writes to the audit log

**Tab 4 · AI Audit** — every call: function, provider, model, `live`/`cache`/`mock`, the
full system and user prompts (CONTEXT block included), the full raw response, latency,
**and the grounding check** — entities named vs entities verified. Nothing hidden.

**Tab 5 · Impact** — the closing numbers from `core/evaluate.py`.

---

## Integration checkpoints

| Time | Check |
|---|---|
| T+0:50 | Lane B's first real `tickets.json` loads and clusters sensibly |
| T+1:10 | Lane C's first real `name_theme` output renders in a card and passes grounding |
| T+1:30 | Full pipeline on real data, real LLM, end to end |
| T+2:00 | **Verify demo ranking** — S1, S2, S3 above background noise; S3 comes out `UNKNOWN` |
| T+2:30 | Freeze. Confirm `LLM_MODE=cache_only` gives an identical dashboard |

---

## Failure modes I am guarding against

- **LLM unreachable on stage** → `cache_only`, verified at T+2:30; `mock` provider below that
- **Clustering splits S1 in two** → merge clusters above a cosine-similarity threshold; if
  that fails, lower the distance threshold and re-verify ranking
- **S3 not recovered** → this is the wow moment. If `classify_novel` misses it, fall back
  to surfacing "11 unclustered Payments tickets in 9 days, no matching category" as an
  *anomaly* card. Less impressive, still honest, still a finding — and still `UNKNOWN`.
- **Grounding validator too strict** (flags legitimate output) → tune the entity
  extractors, never the threshold. A false "unverified" is survivable on stage; a false
  "verified" destroys the claim the whole pitch rests on.
- **Streamlit re-runs the pipeline on every widget click** → `@st.cache_data` on the
  pipeline, keyed on the weight dict; without this the app feels broken on stage
- **A crash during the demo** → every render path wrapped so a missing field degrades to
  "not available" rather than a traceback on the projector
