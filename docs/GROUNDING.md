# GROUNDING — no hallucination, and knowing what we don't know

**This page overrides anything that contradicts it elsewhere.** It comes from the person
who set the challenge, in conversation on the day:

> 1. **Grounding.** The AI must not hallucinate. A decision must not interact with
>    external data.
> 2. **Pattern matching / confidence.** A *seen* case gets a high confidence score. An
>    *unseen* case goes to a human expert. Seed the system with basic categories that are
>    already known.

Both points are now structural in TRACE, not prompt-level wishes. The distinction matters:
"we told the model not to hallucinate" is a hope. "The model physically cannot reference
anything outside the supplied context, and we verify every claim it makes against the
source data before it reaches the screen" is a control.

---

## 1. Closed-world contract

The model sees exactly three things, all drawn from our own dataset:

1. Ticket text from `data/tickets.json`
2. Change records from `data/changes.json`
3. Known-category definitions from `data/categories.json`

And nothing else. Concretely, this means:

| Rule | Enforcement |
|---|---|
| No web access, no search, no browsing | No tools are exposed to the model at all |
| No function calling, no retrieval outside the dataset | Single-turn completion, context assembled by us |
| No appeal to the model's own world knowledge | System prompt states the closed-world rule; the grounding validator catches violations |
| No invented tickets, changes, systems, regions or dates | Validated post-hoc — see §2 |
| Temperature ≤ 0.2 | Reproducibility; the same evidence yields the same finding |

System prompt clause, used by every call:

> Answer **only** from the CONTEXT block below. The context is the complete and only
> permitted source of fact. Do not use prior knowledge about banks, software products,
> vendors or incidents. Do not name any ticket, change, system, region or date that does
> not appear verbatim in the context. If the context is insufficient to answer, say so and
> return a low confidence score. An honest "insufficient evidence" is a correct answer.

The AI's role is deliberately narrow: **it reads and explains evidence we selected
deterministically. It never goes looking.** Root-cause candidates are time-correlated in
`core/rootcause.py` before any model call; the model is handed a ranked shortlist of real
changes and asked to assess them. It cannot propose a cause that is not on that list —
and if it tries, §2 catches it.

---

## 2. The grounding validator — `core/grounding.py`

Deterministic post-processing on **every** model response, before anything renders.

Extract every factual entity the model named, and check it against the context that was
sent:

| Entity | Check |
|---|---|
| `INC-\d{7}` ticket ids | must be in the ticket ids supplied in context |
| `CHG-\d{4}` change ids | must be in the candidate changes supplied in context |
| System names | must be in the system enum **and** present in this theme's tickets |
| Region names | must be in the region enum **and** present in this theme's tickets |
| Dates / date ranges | must fall inside the theme's actual date range |
| Quoted ticket text (`"..."`) | must be a substring of a supplied ticket's title or description |

Result:

```python
{
  "grounded": True,
  "score": 1.0,                 # verified entities / total entities named
  "verified":  [{"kind": "change_id", "value": "CHG-0042"}, ...],
  "unverified": []              # anything that failed
}
```

Consequences, applied automatically:

- `score == 1.0` → the finding renders normally, badged **✓ grounded**
- `0.5 ≤ score < 1.0` → unverified claims are **struck through** in the UI, and
  `confidence` is floored at 0.4
- `score < 0.5` → the AI narrative is **suppressed entirely**; the theme falls back to the
  deterministic summary and routes to a human

Nothing ungrounded ever reaches the user unmarked. The **AI Audit** tab shows the
grounding check for every call — entities named, entities verified — which turns an
abstract claim about safety into something a judge can look at.

Quoting is worth special mention: because quoted text is substring-checked against the
source tickets, a quote on screen is *provably* a real client's words. That is a small
feature with a disproportionate effect on how the demo is received.

---

## 3. Known categories — `data/categories.json`

The seed taxonomy the challenge author asked for. Owned by **Lane D** (same curation job
as the playbooks). Matching is **deterministic** — no model involved in deciding whether
something is known.

```json
{
  "category_id": "CAT-AUTH-001",
  "name": "Authentication / login failure",
  "description": "A client cannot authenticate to a digital channel.",
  "systems": ["MobileApp", "eBanking"],
  "keywords": ["login", "log in", "2fa", "access denied", "biometric", "pin rejected", "locked out"],
  "typical_severity": 3,
  "playbook_id": "PB-LOGIN-001",
  "known_root_causes": [
    "client app version mismatch",
    "expired signing certificate",
    "auth service degradation",
    "credential store corruption after update"
  ],
  "auto_resolve_eligible": true
}
```

`known_root_causes` does double duty: for a **seen** category it is injected into the
prompt as the permitted vocabulary, so the model selects from known causes rather than
inventing one. For an unseen category there is no such list, which is precisely why the
model is not allowed to conclude anything there.

**Match score** (`core/categories.py`, deterministic):

```
keyword_hits  = |theme_keywords ∩ category_keywords| / |category_keywords|
system_match  = 1.0 if theme systems ⊆ category systems, 0.5 if overlapping, 0 otherwise
match_score   = 0.7 * keyword_hits + 0.3 * system_match
```

---

## 4. Three states — seen, variant, unseen

| State | Match | Meaning | AI is allowed to | Routing |
|---|---|---|---|---|
| **KNOWN** | ≥ 0.60 | We have seen this before and have a playbook | describe, and pick a cause **from `known_root_causes` only** | auto-resolve if eligible |
| **KNOWN-VARIANT** | 0.30 – 0.60 | Known category, but behaving unusually — a spike, a new system, an unfamiliar cause | describe, and propose a cause **flagged as outside the known set** | human review, evidence pack pre-built |
| **UNKNOWN** | < 0.30 | Never seen. No playbook exists. | **describe and cluster only — never conclude a cause or an action** | **human expert, mandatory** |

The UNKNOWN restriction is the sharpest expression of the author's point. On a genuinely
novel problem the system's honest output is: *"11 tickets, 9 days, Payments, they belong
together, and here is what they say. I do not know why, and I have no playbook. A human
needs to look at this."* Finding the pattern is the contribution; pretending to know the
cause would be the failure.

How the demo themes land:

| Theme | Match | State | Why it is interesting |
|---|---|---|---|
| S1 mobile login | ~0.85 vs `CAT-AUTH-001` | **KNOWN-VARIANT** | Known category, but the spike and the correlated release are new — so a human sees it despite it being "known" |
| S2 APAC FX | ~0.72 vs `CAT-FX-001` | **KNOWN** but recurring | Playbook exists and has been applied 3× without fixing it — automating it would automate the symptom |
| S3 IBAN | ~0.15 | **UNKNOWN** | No category, no playbook, no cause asserted. The system says "I don't know" and escalates |
| N1–N7 background | 0.7–0.9 | **KNOWN** | The 80% that auto-resolves and never reaches a human |

---

## 5. Confidence is derived, never self-reported

The model's own confidence number is the least trustworthy thing it produces — a model
that hallucinates a cause will happily report 0.9 alongside it. So it is **advisory only,
and it can lower confidence but never raise it**:

```python
confidence = min(
    category_match_confidence,   # deterministic — how well this maps to a known category
    grounding_score,             # deterministic — fraction of the model's claims verified
    llm_stated_confidence,       # advisory — can only pull the number down
)
if state == "UNKNOWN":
    confidence = min(confidence, 0.30)    # hard ceiling: unseen never reaches the auto path
```

Two deterministic checks cap it, and an unseen case is capped below the automation
threshold by construction. **The model cannot talk its way into being trusted** — that is
the sentence to use in Q&A, and it is literally true of the code.

This replaces the earlier design where `confidence` came straight from the LLM.
[SCORING.md](SCORING.md) §3 is updated to match.

---

## 6. Why this scores

- **Technology Innovation** — the interesting engineering is the *constraint*: closed-world
  context, post-hoc entity verification, deterministic confidence. Anyone can call an LLM.
- **Feasibility** — this is the first question a bank's model-risk function asks, and we
  have a structural answer rather than a prompt.
- **Impact** — a risk team can act on a finding that cites verifiable evidence. They
  cannot act on a plausible paragraph.
- **Wow** — the grounding badge and the struck-through unverified claim are visible proof,
  on screen, in a room where every other team will be asserting that their AI is reliable.
