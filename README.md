# TRACE — Ticket Risk & Cause Engine

**UBS Hackathon · Scenario 1 — Ticket Intelligence and Theme Detection**

> From noise to insight: helping risk teams understand what's really going wrong.

Raw tickets → themes → emerging patterns → explainable, actionable insight.
Streamlit dashboard, deterministic clustering, Apertus for the parts that need language
and judgement.

---

## Start here

**Everyone:** read [`PLAN.md`](PLAN.md), then [`docs/SCHEMA.md`](docs/SCHEMA.md), then
your own lane doc. That's about 10 minutes and it is the whole coordination overhead.

| You are | Your doc | First thing to do |
|---|---|---|
| Pipeline + app | [LANE_A_PIPELINE.md](docs/LANE_A_PIPELINE.md) | Scaffold + stubs so nobody is blocked |
| **Synthetic data** | [LANE_B_DATA.md](docs/LANE_B_DATA.md) | **Start now** — spec is complete, no dependencies |
| **Apertus** | [LANE_C_APERTUS.md](docs/LANE_C_APERTUS.md) | Get one call returning parsed JSON |
| **Playbooks + pitch** | [LANE_D_PITCH.md](docs/LANE_D_PITCH.md) | Write `data/playbooks.json`, then the pitch |

Lanes B and D can start immediately with no code from anyone else. Lane C can start on
parsing and caching against any OpenAI-compatible endpoint while we wait for the Apertus
credentials.

## Reference

- [docs/SCHEMA.md](docs/SCHEMA.md) — **the frozen data contracts.** Read before writing code.
- [docs/SCORING.md](docs/SCORING.md) — signals, risk score, triage gate
- [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) — the 3-minute beat sheet + what's mocked
- [Case_information.md](Case_information.md) — the original brief
- [Ideas.md](Ideas.md) — the brainstorm this came out of

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add Apertus credentials
streamlit run app.py
```

Check a data file without running the app:

```bash
python -m core.schema data/tickets.json
```

## The one-line pitch

Deterministic clustering handles the bulk of the volume; Apertus handles language,
reasoning and novelty. Cost scales with **themes**, not tickets — about twenty model calls
per run whether that run covers a thousand tickets or a hundred thousand. Every score
decomposes into its components, every root cause cites its evidence, every AI call is
logged with its prompt and response, and low confidence always routes to a human.
