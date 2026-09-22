# LANE C — Apertus integration

**You own:** `ai/apertus.py`, `ai/prompts.py`, `data/cache/llm_cache.json`
**You must not edit:** anything in `core/`, `gen/`, `app.py`
**Read first:** [SCHEMA.md](SCHEMA.md) §4 (theme shape) and §5 (audit entry).

**Your deadline: one real Apertus call returning parsed JSON by T+0:50.** Everything
after that is prompt quality. Getting auth + response format working is the risk; do it
first, before writing a single good prompt.

---

## What Lane A calls

Three functions. These signatures are **frozen** — Lane A is already calling them
against stubs. Implement exactly these, in `ai/apertus.py`:

```python
def name_theme(tickets: list[dict], context: dict) -> dict: ...
def explain_root_cause(theme: dict, candidate_changes: list[dict], stats: dict) -> dict: ...
def classify_novel(ticket: dict, known_themes: list[dict]) -> dict: ...
```

### `name_theme(tickets, context)`

Given a cluster of tickets, produce a human-readable theme name and summary.

- `tickets` — up to 15 sampled tickets from the cluster (Lane A samples; you do not
  need to truncate further). Each is a ticket dict **without** `_gt_theme` — the
  ground-truth field is stripped before it reaches you. Never ask for it.
- `context` — `{"cluster_size": 258, "keywords": [...], "systems": [...], "regions": [...], "date_range": ["...", "..."]}`

Returns:

```python
{
  "name": "Mobile login failures after 4.2.0 auth SDK migration",  # ≤ 10 words
  "summary": "Clients on MobileApp 4.2.0 cannot authenticate...",   # 1–2 sentences
  "confidence": 0.86,                          # float 0–1
  "evidence_ticket_ids": ["INC-0001234", ...], # 2–3 ids that best typify the theme
  "_raw": { ... }                              # see "_raw" below
}
```

### `explain_root_cause(theme, candidate_changes, stats)`

The heart of the demo. Lane A has **already** done the time correlation and hands you a
shortlist — you are not searching, you are *reasoning over pre-computed evidence and
writing it up*. Do not invent changes that are not in `candidate_changes`.

- `theme` — the theme dict (see SCHEMA §4), with `ticket_ids` and a sample of tickets
  under `theme["sample_tickets"]`
- `candidate_changes` — ranked list, each `{change_id, title, system, type, regions, deployed_at, lag_hours, system_match, region_overlap, linked_ticket_count}`
- `stats` — `{"onset": "...", "peak_day": "...", "baseline_per_day": 2.1, "peak_per_day": 62, "systems": [...], "regions": [...], "episodes": 1}`

Returns:

```python
{
  "hypothesis": "The 4.2.0 auth SDK migration...",   # 1–2 sentences, the cause
  "contributing_factors": [                           # 2–4 bullets
    "Rollout was global rather than staged, so all regions were exposed at once",
    "Biometric re-enrolment was not triggered by the migration"
  ],
  "confidence": 0.81,
  "evidence": [                                       # what you actually leaned on
    {"kind": "change_correlation", "change_id": "CHG-0042", "detail": "spike onset 3.2h after deploy"},
    {"kind": "linked_tickets",     "count": 31,        "detail": "31 tickets explicitly reference CHG-0042"},
    {"kind": "ticket_quote",       "ticket_id": "INC-0001234", "detail": "\"Access Denied after entering PIN\""}
  ],
  "_raw": { ... }
}
```

**Hard prompt rule:** if the evidence is weak, the model must say so and return a low
`confidence`. A hedged "the timing is suggestive but two other changes landed in the same
window" is *worth more* to us than false certainty — it is what a risk function actually
wants, and a judge will test exactly this in Q&A. Put that instruction in the system
prompt explicitly.

`evidence[].kind` is one of `change_correlation` `linked_tickets` `ticket_quote`
`temporal_pattern` `region_concentration`. Lane A renders each kind with its own icon,
so stick to the enum.

### `classify_novel(ticket, known_themes)`

For tickets Stage 1 could not cluster. This is what catches storyline **S3**.

- `ticket` — one ticket dict
- `known_themes` — `[{"theme_id": "T-01", "name": "...", "summary": "..."}, ...]`

Returns:

```python
{
  "theme_id": "T-03" | None,   # None means "this does not fit any known theme"
  "is_new": False,
  "confidence": 0.74,
  "reason": "Describes the same beneficiary-validation rejection as T-03, phrased as a client complaint",
  "_raw": { ... }
}
```

When `theme_id` is `None` and `is_new` is `True`, Lane A groups those tickets and runs a
second pass to name the emergent theme. **S3's 11 tickets have no shared keyword, so
Stage 1 will leave them as singletons and this function is the only thing that finds
them.** If `classify_novel` works well, the demo has its wow moment; if it does not, we
lose the best 20 seconds of the pitch. Prioritise this function's prompt over polishing
`name_theme`.

---

## The `_raw` field — non-negotiable

Every return value carries `_raw`, and Lane A's audit log depends on it:

```python
"_raw": {
  "model": "apertus-70b-instruct",
  "prompt": "<the full prompt text you sent, system + user concatenated>",
  "response": "<the full raw response text, before parsing>",
  "source": "live" | "cache",
  "latency_ms": 1840
}
```

No `_raw`, no audit entry, and the "explainability" claim in our pitch is a lie. This is
the single most important thing your module does after returning useful content.

---

## Configuration

`.env` — keep the real key out of any file you share; `.env.example` holds the blank
template:

```bash
APERTUS_API_KEY=...
APERTUS_BASE_URL=...            # fill in when we have it
APERTUS_MODEL=...               # fill in when we have it
APERTUS_MODE=cache_first        # live | cache_first | cache_only
APERTUS_TIMEOUT=25
```

`APERTUS_MODE` semantics — implement all three:

| Mode | Behaviour |
|---|---|
| `live` | always call the API, write every result to the cache |
| `cache_first` | cache hit → return it; miss → call the API and store. **Default during build.** |
| `cache_only` | cache hit → return it; miss → return a safe stub with `confidence: 0.0` and never touch the network. **This is what runs on stage.** |

Cache key: `sha256(function_name + "|" + model + "|" + prompt_text)`.

Cache file `data/cache/llm_cache.json`, a single object:

```json
{
  "3f9a2c...": {
    "function": "name_theme",
    "model": "apertus-70b-instruct",
    "prompt": "...",
    "response": "...",
    "parsed": { "name": "...", "summary": "...", "confidence": 0.86 },
    "created_at": "2026-09-22T14:03:11Z"
  }
}
```

**Keep the cache file with the project and make sure the presenting laptop has it.** It is
the demo's safety net, and it lets Lane D take screenshots without burning API calls.

---

## Robustness — assume the model misbehaves

Apertus is an open model; do not assume clean JSON. Build this from the start, not after
it bites you at T+1:45:

1. **Ask for JSON explicitly** in the system prompt, and give a filled-in example of the
   exact object you want. Few-shot beats instructions.
2. **Extract, don't trust.** Pull the outermost `{...}` from the response with a regex
   before `json.loads`. Strip ```` ```json ```` fences.
3. **Retry once** on a parse failure, appending *"Your previous reply was not valid JSON.
   Reply with the JSON object only, no prose."*
4. **Never raise into Lane A.** On total failure, return a valid object with
   `confidence: 0.0` and a `name` like `"Unnamed cluster (AI unavailable)"`. The app must
   render. A dashboard that crashes on stage scores zero on all four criteria.
5. **Low temperature** (~0.2) — we want reproducibility, not creativity.

Write a `_call(prompt, system) -> tuple[str, dict]` helper that handles auth, timeout,
retry, caching and `_raw` construction once, and have all three functions use it. Do not
duplicate that logic three times.

---

## Prompt guidance

Put all templates in `ai/prompts.py` as module-level strings so they are diffable and
Lane A never has to touch your call logic to tweak wording.

System prompt spine — reuse across all three:

> You are an operational-risk analyst at a large bank. You analyse incident tickets and
> report findings to a risk committee. Be precise and concise. Base every statement only
> on the evidence provided — never invent systems, changes, dates or numbers that are not
> in the input. If the evidence is weak or ambiguous, say so and lower your confidence
> score. Reply with a single JSON object and nothing else.

For `explain_root_cause`, add:

> You are given candidate changes that were already time-correlated with this theme.
> Assess whether any of them plausibly caused it. Consider: the lag between deployment and
> ticket onset, whether the affected system matches, whether the affected regions overlap,
> and whether other changes in the same window could explain it equally well. If a
> competing change explains the pattern just as well, say so and lower your confidence.

That last sentence is what makes the output sound like a risk professional rather than a
chatbot, and it is what survives Q&A.

---

## Interim stub (delete once real calls work)

Lane A ships a stub at `ai/apertus.py` so the app runs from T+0:20. **Replace it, keep the
signatures.** If you need to work before we have the key, point `APERTUS_BASE_URL` at any
OpenAI-compatible endpoint (or a local Ollama) to develop the parsing and caching logic,
then swap the base URL when the Apertus credentials arrive. The parsing, retry and cache
layers are the slow part — write those against *anything* rather than idling.

---

## Definition of done

- [ ] All three functions return schema-valid dicts with populated `_raw`
- [ ] All three modes (`live` / `cache_first` / `cache_only`) work
- [ ] Malformed JSON from the model is recovered or degraded safely — never raises
- [ ] `classify_novel` correctly groups S3's 11 IBAN tickets (ask Lane B to test with you)
- [ ] `explain_root_cause` names `CHG-0042` for S1 and expresses appropriate uncertainty for S2
- [ ] `data/cache/llm_cache.json` populated for the full demo run and on the demo laptop
- [ ] At T+2:30 you confirm in chat: **"cache frozen, cache_only verified"**
