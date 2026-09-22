# LANE D — Playbooks, pitch and demo

**You own:** `data/categories.json`, `data/playbooks.json`, `slides/`, [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md)
**You must not edit:** `core/`, `ai/`, `gen/`, `app.py`
**Read first:** [GROUNDING.md](GROUNDING.md), then [SCHEMA.md](SCHEMA.md) §3–§4 and [SCORING.md](SCORING.md)

Three jobs: two small curated data files the app actually consumes, then the thing that
wins or loses us the points. **Half the score (Wow Factor + Impact = 20 of 40) is decided by how the
last three minutes go, not by how good the code is.** Treat the pitch as the deliverable,
not the write-up.

---

## Job 1 — `data/categories.json` *(do this first, ~20 minutes)*

The seed catalog of known problems — the thing the challenge author explicitly asked for.
Schema in [SCHEMA.md §4](SCHEMA.md#4-category--datacategoriesjson), semantics in
[GROUNDING.md §3](GROUNDING.md#3-known-categories--datacategoriesjson).

This file is what lets the system distinguish *seen* from *unseen*, which is the whole
basis of when a human has to step in. It matters more than the playbooks.

**8–10 categories**, one per background theme plus authentication and FX:

| `category_id` | Covers | `playbook_id` |
|---|---|---|
| `CAT-AUTH-001` | Authentication / login failure | `PB-LOGIN-001` |
| `CAT-PWD-001` | Password reset / account unlock | `PB-PWD-001` |
| `CAT-DOC-001` | Statement or document download | `PB-DOC-001` |
| `CAT-CARD-001` | Card blocked while travelling | `PB-CARD-001` |
| `CAT-RPT-001` | Reporting performance | `PB-RPT-001` |
| `CAT-ONB-001` | Onboarding document rejected | `PB-ONB-001` |
| `CAT-PAY-001` | Payment limits and beneficiaries | `PB-PAY-001` |
| `CAT-HW-001` | Branch device / peripheral | `PB-HW-001` |
| `CAT-FX-001` | FX settlement break | `PB-FX-001` |

**Critically: no category may match storyline S3** (the Austrian IBAN validation issue).
It has to come out `UNKNOWN`. Watch `CAT-PAY-001` in particular — keep its keywords on
*limits*, *standing order amount*, *beneficiary not saved*, and **off** *IBAN*, *invalid*,
*format*, *rejected*. If S3 accidentally matches a category, the best twenty seconds of
the demo evaporate. Test it with Lane B and Lane A before you call this done.

`known_root_causes` is the model's permitted vocabulary for a seen category — 3–5 realistic
causes each. Write them as an engineer would log them, not as marketing copy.

---

## Job 2 — `data/playbooks.json` *(~20 minutes)*

8–10 playbooks. Schema and an example in [SCHEMA.md §3](SCHEMA.md#3-playbook--dataplaybooksjson).

Cover these, matching Lane B's themes:

| Playbook | For | `auto_resolve_eligible` |
|---|---|---|
| Authentication failure after client app update | S1 mobile login | `true` |
| Password reset / account unlock | N1 | `true` |
| Statement or document download failure | N2 | `true` |
| Card blocked while travelling | N3 | `true` |
| Reporting performance at month-end | N4 | `false` |
| Onboarding document rejected | N5 | `true` |
| Payment limit and beneficiary queries | N6 | `true` |
| Branch device / peripheral fault | N7 | `false` |
| FX settlement break — manual re-sync | S2 | **`false`** |

Two deliberate gaps, and they both earn their keep on stage:

- **No playbook for S3** (the Austrian IBAN issue) — so it routes to a human because
  nothing known covers it. That is the system behaving correctly on a genuinely new
  problem, and it is worth pointing at for five seconds.
- **S2's playbook is `auto_resolve_eligible: false`** — the "fix" is a manual re-sync that
  has already been applied three times without solving anything. Automating it would
  automate the *symptom*. Good line: *"the playbook exists, and that's exactly the
  problem — we've been auto-resolving a control failure for three months."*

Make `avg_resolution_minutes` realistic (15–45) — it drives the hours-saved number, and
if it is inflated the impact tile becomes indefensible under questioning.

All `self_service_link` values use an `*.example` domain. They are mocked and we say so.

Validate both before handing over:
```bash
python -m core.schema data/categories.json
python -m core.schema data/playbooks.json
```

---

## Job 3 — the pitch

### Timing

3 minutes is brutally short. **Rehearse against a timer, at least twice.** Almost every
hackathon team runs 4:30 on their first attempt and gets cut off before the payoff.

Rough split: **~25s framing · ~135s live demo · ~20s impact and close.** The demo is the
pitch. Do not build slides that duplicate what is on the screen.

### Slides — four, maximum

1. **Title** — TRACE, the tagline, four names
2. **The problem** — one sentence and one number. *"A risk analyst opens 1,400 tickets on
   Monday morning and has no way to see which four things actually matter."*
3. *(the demo runs here — no slide)*
4. **How it scales + what's mocked** — the two-stage diagram, the cost line
   (~20 LLM calls per run regardless of ticket volume), the mocked list
5. **Impact** — the numbers, each labelled measured or assumed

### The three things that must be said

Pick one person to say each, so nobody forgets:

1. **"AI where it earns its cost."** Deterministic clustering handles the bulk; the model
   handles language, reasoning and novelty. Cost scales with *themes*, not tickets.
2. **"Nothing on this screen is unexplained."** Every score decomposes, every root cause
   cites evidence, every AI call is logged with its prompt and response.
3. **"The system is allowed to say it doesn't know."** We seed it with the categories we
   have seen before. Anything outside them is capped below the automation threshold and
   goes to a human expert — and on an unseen problem the model is not permitted to state a
   cause at all, only to show you the pattern it found.

Plus, if there is time for a fourth: **"nothing the model says reaches the screen
unverified."** Every ticket id, change id, system, date and quote is checked against the
source data before it renders.

### What NOT to do

- Don't read the slides. Don't explain the architecture before showing the product.
- Don't say "AI-powered" without immediately saying *which part* and *why there*.
- Don't hide the mocked data. Declare it in one confident sentence — it is required, and
  hedging about it looks worse than the mocking itself.
- Don't let the demo driver narrate their clicking. One person drives silently, one
  person talks.

---

## Q&A prep (2 minutes, expect 3–4 questions)

Write these on a card. Answers are short on purpose.

**"How do you know the clusters are right?"**
> We planted eight known themes in the synthetic data and measured recovery against them —
> that's the purity number on the impact tile. On real data you'd calibrate the same way
> against a labelled sample.

**"Why not just use an LLM for everything?"**
> Cost and auditability. 1,400 tickets would be 1,400 calls; we make about twenty. And the
> deterministic stage is reproducible — same input, same clusters, every time. That matters
> to a risk function.

**"What stops the AI hallucinating a root cause?"** *(the question the challenge author
cares about — know this one cold)*
> Three things, none of them a prompt. One: closed world — the model only sees a context
> block we build from our own tickets and change log, no tools, no web, no retrieval.
> Two: it never searches for a cause; we time-correlate deterministically and hand it a
> shortlist of real changes to assess. Three: we verify afterwards — every ticket id,
> change id, system, date and quote it produced is checked against the source data. Fails
> the check, it gets struck through or suppressed. And on an unseen problem it isn't
> allowed to propose a cause at all.

**"How does it know what it hasn't seen before?"**
> We seed it with a catalog of known problem categories, and matching against that catalog
> is deterministic — no model decides whether something is known. Above a match threshold
> it's KNOWN and can be automated; in the middle it's a known category behaving oddly, so a
> human sees it; below, it's UNKNOWN and goes to a human expert with the confidence capped
> at 0.3. The IBAN theme in the demo is exactly that case.

**"Isn't the confidence score just the model's own guess?"**
> No — that's the one number we don't trust. Confidence is the minimum of the category
> match, the grounding score, and what the model claims. The model can only lower it. It
> cannot talk its way into being trusted.

**"How would this actually get deployed at UBS?"**
> Ingestion is one adapter — ServiceNow or Jira into the ticket schema. The model sits
> behind one interface, so it can be a hosted API or a model running inside the bank; we
> swap it with an environment variable and no code change, which also means ticket text
> never has to leave if policy says it can't. The pipeline is a scheduled batch job,
> hourly. The dashboard is the only new surface.

**"Who picked those risk weights?"**
> We did, arbitrarily — and they shouldn't be ours. They're a policy input, which is why
> they're sliders. A risk function calibrates them to its own appetite, then measures
> override rates to recalibrate.

**"What's real and what's mocked?"**
> Data is synthetic and the playbook links go nowhere. Clustering, scoring, the model
> calls and the audit log are all real. *(Know this cold — it will be asked.)*

**"What if the categories are wrong or incomplete?"**
> Then themes land as UNKNOWN and go to humans — which is the safe direction to fail. Every
> expert decision on an unknown theme is logged, and that's how the catalog grows: a
> resolved unknown becomes a new seed category.

**"What would you build next?"**
> Feedback loop. Every human override is already logged; that's labelled training data for
> threshold calibration and, eventually, for routing. The system should get better at
> knowing when to ask.

---

## Definition of done

- [ ] `data/categories.json` validates, 8–10 entries, covering the table above
- [ ] **S3 (IBAN) matches no category** — verified with Lane A, not assumed
- [ ] `known_root_causes` written for every category, 3–5 each
- [ ] `data/playbooks.json` validates, 8–10 entries, covering the table above
- [ ] No playbook for S3; S2's playbook is `auto_resolve_eligible: false`
- [ ] Four slides, no more
- [ ] [DEMO_SCRIPT.md](DEMO_SCRIPT.md) beat sheet confirmed against the real app
- [ ] Mocked-parts list current and on a slide
- [ ] Q&A card written, one owner per answer
- [ ] **Two timed rehearsals done, both under 3:00**
- [ ] Screenshots of the working dashboard saved as a fallback if the laptop dies
