# TRACE — Ticket Risk & Cause Engine

**UBS Hackathon · Scenario 1 — Ticket Intelligence and Theme Detection**

> From noise to insight: helping risk teams understand what's really going wrong.

Raw tickets → themes → emerging patterns → explainable, actionable insight.
Streamlit dashboard, deterministic clustering, an LLM (OpenAI or Gemini) for the parts
that need language and judgement — grounded, verified, and honest about what it hasn't
seen before.

---

## Start here

**Everyone:** read [`PLAN.md`](PLAN.md), then [`docs/SCHEMA.md`](docs/SCHEMA.md) and
[`docs/GROUNDING.md`](docs/GROUNDING.md), then your own lane doc. About 15 minutes, and it
is the whole coordination overhead.

| You are | Your doc | First thing to do |
|---|---|---|
| Pipeline + app | [LANE_A_PIPELINE.md](docs/LANE_A_PIPELINE.md) | Scaffold + stubs so nobody is blocked |
| **Synthetic data** | [LANE_B_DATA.md](docs/LANE_B_DATA.md) | **Start now** — spec is complete, no dependencies |
| **LLM (OpenAI/Gemini)** | [LANE_C_LLM.md](docs/LANE_C_LLM.md) | Get one call returning parsed JSON |
| **Categories, playbooks + pitch** | [LANE_D_PITCH.md](docs/LANE_D_PITCH.md) | Write `data/categories.json`, then playbooks, then the pitch |

Lanes B and D can start immediately with no code from anyone else. Lane C can start on
parsing, caching and the provider abstraction against the built-in `mock` provider while
we wait for an API key.

## Reference

- [docs/SCHEMA.md](docs/SCHEMA.md) — **the frozen data contracts.** Read before writing code.
- [docs/GROUNDING.md](docs/GROUNDING.md) — **no-hallucination contract**, seed categories,
  seen vs unseen, how confidence is derived. Binding on every lane.
- [docs/SCORING.md](docs/SCORING.md) — signals, risk score, triage gate
- [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) — the 3-minute beat sheet + what's mocked
- [Case_information.md](Case_information.md) — the original brief
- [Ideas.md](Ideas.md) — the brainstorm this came out of

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add an OpenAI or Gemini key (optional: mock provider works offline)
streamlit run app.py
```

Check a data file without running the app:

```bash
python -m core.schema data/tickets.json
```

## The one-line pitch

Deterministic clustering handles the bulk of the volume; the model handles language,
reasoning and novelty. Cost scales with **themes**, not tickets — about twenty calls per
run whether that run covers a thousand tickets or a hundred thousand.

The model works in a closed world: it only ever sees a context block built from our own
tickets and change log, it never searches for a root cause (we correlate deterministically
and hand it a shortlist), and every entity it names is verified against the source data
before it reaches the screen. Problems we have seen before are matched against a seed
category catalog and can be automated. Problems we have not seen are capped below the
automation threshold, and the model is not permitted to state a cause for them at all —
it shows the pattern and hands it to a human expert.
