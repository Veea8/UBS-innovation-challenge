# LANE C — LLM integration (OpenAI / Gemini)

**You own:** `ai/llm.py`, `ai/prompts.py`, `data/cache/llm_cache.json`
**You must not edit:** anything in `core/`, `gen/`, `app.py`
**Read first:** [GROUNDING.md](GROUNDING.md) — it constrains everything you write here.
Then [SCHEMA.md](SCHEMA.md) §4–§5.

> **Changed:** Apertus is out. The challenge author didn't care about the model choice, so
> we use whatever is reliable. Build **provider-agnostic** — OpenAI and Gemini behind one
> interface. Keys will follow; start now against the `mock` provider.

**Your deadline: one real call returning parsed, schema-valid JSON by T+0:50.** Auth and
response-format wrangling is the risk. Do that before writing a single good prompt.

---

## Your actual job, in one line

You are not building "the AI part". You are building a **narrow, verifiable reader** that
explains evidence someone else already selected. Everything in [GROUNDING.md](GROUNDING.md)
is your specification, not background reading — the closed-world prompt rule, the fact
that `core/grounding.py` will verify every entity you return, and the fact that your
`confidence` number can only ever lower the final score. Build for that from the start.

---

## Provider abstraction

`ai/llm.py`:

```python
def complete(system: str, user: str, *, max_tokens: int = 800) -> tuple[str, dict]:
    """Returns (response_text, raw_meta). The ONLY place a provider SDK is touched."""
```

Selected by `LLM_PROVIDER`:

| Provider | Call | JSON enforcement |
|---|---|---|
| `openai` | `chat.completions.create(model=..., messages=[system, user], temperature=0.1)` | `response_format={"type": "json_object"}` |
| `gemini` | `models.generate_content(...)` | `generation_config={"response_mime_type": "application/json"}` |
| `mock` | returns canned fixtures | trivially valid |

Both SDKs are in `requirements.txt`; import lazily inside the provider branch so a missing
key for one provider never breaks the other. `mock` must work with **no key and no
network** — Lane D needs it for screenshots and it is the fallback if both keys fail.

The three public functions below must be **provider-unaware**. If `complete()` is written
properly, switching provider is one env var and zero code changes — which is also a good
Q&A answer about vendor lock-in.

---

## The three functions Lane A calls

Signatures are **frozen** — Lane A is already calling them against stubs.

```python
def name_theme(tickets: list[dict], context: dict) -> dict: ...
def explain_root_cause(theme: dict, candidate_changes: list[dict], stats: dict, category: dict | None) -> dict: ...
def classify_novel(ticket: dict, known_themes: list[dict], categories: list[dict]) -> dict: ...
```

### `name_theme(tickets, context)`

- `tickets` — up to 15 sampled tickets, already stripped of `_`-prefixed ground truth
- `context` — `{"cluster_size", "keywords", "systems", "regions", "date_range"}`

```python
{
  "name": "Mobile login failures after 4.2.0 auth SDK migration",  # ≤ 10 words
  "summary": "...",                             # 1–2 sentences
  "confidence": 0.86,
  "evidence_ticket_ids": ["INC-0001234", ...],  # 2–3 ids, must exist in input
  "_raw": { ... }
}
```

### `explain_root_cause(theme, candidate_changes, stats, category)`

The centrepiece, and the one most constrained by grounding.

- `candidate_changes` — a **ranked shortlist already time-correlated by
  `core/rootcause.py`**. You assess; you never search. Naming a change outside this list
  fails the grounding check and the whole narrative gets suppressed.
- `category` — the matched known category, or `None`

**Branch on the category state** (see [GROUNDING.md §4](GROUNDING.md#4-three-states--seen-variant-unseen)):

| State | What you ask the model for |
|---|---|
| `KNOWN` | Pick a cause **from `category["known_root_causes"]` only.** Include that list in the prompt and say it is the only permitted set. |
| `KNOWN-VARIANT` | Known category, anomalous behaviour. A cause outside the known set is allowed but must be returned with `"outside_known_causes": true`. |
| `UNKNOWN` | **Do not ask for a cause at all.** Ask only for a neutral description of what the tickets have in common. Return `hypothesis: None`. |

That last row is the one to get right — it is the challenge author's point made concrete,
and it is where a normal implementation would quietly hallucinate.

```python
{
  "hypothesis": "..." | None,
  "contributing_factors": ["...", "..."],       # 2–4, [] when UNKNOWN
  "confidence": 0.81,
  "outside_known_causes": False,
  "evidence": [
    {"kind": "change_correlation", "change_id": "CHG-0042", "detail": "spike onset 3.2h after deploy"},
    {"kind": "linked_tickets", "count": 31, "detail": "31 tickets reference CHG-0042"},
    {"kind": "ticket_quote", "ticket_id": "INC-0001234", "detail": "\"Access Denied after entering PIN\""}
  ],
  "_raw": { ... }
}
```

`evidence[].kind` ∈ `change_correlation` `linked_tickets` `ticket_quote`
`temporal_pattern` `region_concentration`. Lane A renders one icon per kind.

**Quotes must be verbatim** — `core/grounding.py` substring-checks them against the source
ticket. Paraphrase it and the claim gets struck through on screen.

### `classify_novel(ticket, known_themes, categories)`

Runs on tickets Stage 1 could not cluster. This is what catches storyline **S3**.

```python
{
  "theme_id": "T-03" | None,
  "is_new": False,
  "confidence": 0.74,
  "reason": "Same beneficiary-validation rejection as T-03, phrased as a client complaint",
  "_raw": { ... }
}
```

**Prioritise this function's prompt over polishing `name_theme`.** S3's 11 tickets share
no keyword, so Stage 1 leaves them as singletons and this is the only thing that finds
them. It is the best 20 seconds of the pitch.

---

## `_raw` — non-negotiable

Every return value carries it. No `_raw`, no audit entry, no grounding check, and our
explainability claim becomes a lie.

```python
"_raw": {
  "provider": "openai",
  "model": "gpt-4.1",
  "system": "<full system prompt>",
  "user": "<full user prompt, including the CONTEXT block>",
  "response": "<full raw response text, before parsing>",
  "source": "live" | "cache" | "mock",
  "latency_ms": 1840,
}
```

`core/grounding.py` re-reads `_raw["user"]` to know what the model was allowed to see.
If the context block isn't captured verbatim, grounding cannot be verified.

---

## Configuration

`.env` — keep real keys out of anything you share:

```bash
LLM_PROVIDER=mock          # openai | gemini | mock
LLM_MODE=cache_first       # live | cache_first | cache_only
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
LLM_TIMEOUT=25
LLM_TEMPERATURE=0.1
```

| `LLM_MODE` | Behaviour |
|---|---|
| `live` | always call, write every result to cache |
| `cache_first` | hit → return; miss → call and store. **Default during build.** |
| `cache_only` | hit → return; miss → safe stub with `confidence: 0.0`. Never touches the network. **This is what runs on stage.** |

Cache key: `sha256(function + "|" + provider + "|" + model + "|" + system + "|" + user)`.
Cache file `data/cache/llm_cache.json`, one object keyed by that hash, each entry storing
`{function, provider, model, system, user, response, parsed, created_at}`.

Keep the cache with the project and make sure it is on the demo laptop.

---

## Robustness — assume the model misbehaves

Build this now, not at T+1:45 when it bites.

1. **Ask for JSON explicitly** and give a filled-in example of the exact object. Few-shot
   beats instructions, on every provider.
2. **Extract, don't trust** — pull the outermost `{...}` with a regex before `json.loads`;
   strip ```` ```json ```` fences. Gemini adds them even in JSON mode.
3. **Retry once** on a parse failure with *"Your previous reply was not valid JSON. Reply
   with the JSON object only."*
4. **Never raise into Lane A.** On total failure return a valid object with
   `confidence: 0.0` and `"name": "Unnamed cluster (LLM unavailable)"`. The app must
   render — a crash on the projector scores zero on all four criteria.
5. **Temperature 0.1.** We want reproducibility, not creativity.

Write `_call()` once, handling auth, timeout, retry, caching and `_raw`. All three
functions go through it. Do not duplicate that logic three times.

---

## Prompts

All templates in `ai/prompts.py` as module-level strings, so they are diffable and Lane A
never touches your call logic to tweak wording.

**System prompt spine** — every call, verbatim from [GROUNDING.md §1](GROUNDING.md#1-closed-world-contract):

> You are an operational-risk analyst at a large bank. You analyse incident tickets and
> report findings to a risk committee.
>
> Answer **only** from the CONTEXT block below. The context is the complete and only
> permitted source of fact. Do not use prior knowledge about banks, software products,
> vendors or incidents. Do not name any ticket, change, system, region or date that does
> not appear verbatim in the context. Quote ticket text exactly or not at all.
>
> If the context is insufficient, say so and return a low confidence score. An honest
> "insufficient evidence" is a correct answer and is preferred over a plausible guess.
>
> Reply with a single JSON object and nothing else.

For `explain_root_cause`, add:

> You are given candidate changes that were already time-correlated with this theme. You
> may only consider these; do not propose any other cause. Assess the lag between
> deployment and ticket onset, whether the affected system matches, whether regions
> overlap, and whether a competing change in the same window explains the pattern equally
> well. If one does, say so and lower your confidence.

Mark the context block clearly so the boundary is unambiguous to the model *and* to a
judge reading the audit tab:

```
=== CONTEXT (the only permitted source of fact) ===
...tickets, changes, category...
=== END CONTEXT ===
```

---

## Definition of done

- [ ] `openai`, `gemini` and `mock` providers all work behind `complete()`
- [ ] `mock` works with no key and no network
- [ ] All three functions return schema-valid dicts with populated `_raw` including the verbatim context
- [ ] `UNKNOWN` state returns `hypothesis: None` — verified, not assumed
- [ ] `KNOWN` state picks only from `known_root_causes`
- [ ] Malformed JSON is recovered or degraded safely — never raises
- [ ] All three `LLM_MODE`s work
- [ ] `classify_novel` groups S3's 11 IBAN tickets (test this with Lane B)
- [ ] `explain_root_cause` names `CHG-0042` for S1 and shows real uncertainty on S2
- [ ] Cache populated for the full demo run and on the demo laptop
- [ ] At T+2:30 confirm in chat: **"cache frozen, cache_only verified"**
