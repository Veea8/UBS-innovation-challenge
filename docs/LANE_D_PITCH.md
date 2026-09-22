# LANE D — Playbooks, pitch and demo

**You own:** `data/playbooks.json`, `slides/`, [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md)
**You must not edit:** `core/`, `ai/`, `gen/`, `app.py`
**Read first:** [SCHEMA.md](SCHEMA.md) §3, [SCORING.md](SCORING.md)

Two jobs: a small data file the app actually consumes, then the thing that wins or loses
us the points. **Half the score (Wow Factor + Impact = 20 of 40) is decided by how the
last three minutes go, not by how good the code is.** Treat the pitch as the deliverable,
not the write-up.

---

## Job 1 — `data/playbooks.json` *(do this first, ~25 minutes)*

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

Validate before handing over:
```bash
python -m core.schema data/playbooks.json
```

---

## Job 2 — the pitch

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

1. **"AI where it earns its cost."** Deterministic clustering handles the bulk; Apertus
   handles language, reasoning and novelty. Cost scales with *themes*, not tickets.
2. **"Nothing on this screen is unexplained."** Every score decomposes, every root cause
   cites evidence, every AI call is logged with its prompt and response.
3. **"The system is allowed to say it doesn't know."** Low confidence always routes to a
   human. That is what makes it deployable in a bank.

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

**"What stops the AI hallucinating a root cause?"**
> It never searches for a cause. We do the time-correlation deterministically and hand it a
> ranked shortlist of real changes; it reasons over those and cites which ones. And it's
> instructed to lower its confidence when the evidence is weak — you can see it do that on
> the FX theme.

**"How would this actually get deployed at UBS?"**
> Ingestion is one adapter — ServiceNow or Jira into the ticket schema. Apertus is a Swiss
> open model, so it can be hosted inside the bank; no ticket text leaves. The pipeline is a
> scheduled batch job, hourly. The dashboard is the only new surface.

**"Who picked those risk weights?"**
> We did, arbitrarily — and they shouldn't be ours. They're a policy input, which is why
> they're sliders. A risk function calibrates them to its own appetite, then measures
> override rates to recalibrate.

**"What's real and what's mocked?"**
> Data is synthetic and the playbook links go nowhere. Clustering, scoring, the Apertus
> calls and the audit log are all real. *(Know this cold — it will be asked.)*

**"What would you build next?"**
> Feedback loop. Every human override is already logged; that's labelled training data for
> threshold calibration and, eventually, for routing. The system should get better at
> knowing when to ask.

---

## Definition of done

- [ ] `data/playbooks.json` validates, 8–10 entries, covering the table above
- [ ] No playbook for S3; S2's playbook is `auto_resolve_eligible: false`
- [ ] Four slides, no more
- [ ] [DEMO_SCRIPT.md](DEMO_SCRIPT.md) beat sheet confirmed against the real app
- [ ] Mocked-parts list current and on a slide
- [ ] Q&A card written, one owner per answer
- [ ] **Two timed rehearsals done, both under 3:00**
- [ ] Screenshots of the working dashboard saved as a fallback if the laptop dies
