# Solving the grounding issue

## The problem

Ticket clustering is useful only when its explanation can be checked. A plausible
root cause is not evidence. The system must therefore separate three jobs:

1. **Discover a pattern** from ticket text, system, region, and time.
2. **Correlate evidence** against change records that really exist in the supplied data.
3. **Route uncertainty** instead of inventing a cause for a new or weakly supported pattern.

The pipeline is closed-world: it reads only `data/tickets.json` and
`data/changes.json`. Fields beginning with `_`, including `_gt_theme`, are evaluation
metadata and are never used to assign a cluster or explain one.

## Deterministic strategy

`scripts/grounded_cluster.py` applies the following steps:

### 1. Normalize and score ticket text

Each ticket is compared with a fixed vocabulary of known categories. A category score is
computed from:

- keyword coverage in the title and description: 70%
- system compatibility: 30%

The winning category must also meet a minimum ticket score. Otherwise the ticket is
assigned to `unclassified` rather than forced into a known theme.

### 2. Build clusters without ground truth

Tickets with the same winning rule are grouped together. The cluster output contains the
actual ticket IDs, systems, regions, date range, matched terms, and counts. This makes the
description reproducible from source fields rather than from an invented summary.

### 3. Rank only real change records

For each cluster, changes are candidates only when they:

- have the same system as the cluster;
- include at least one cluster region;
- occurred before the first ticket and within the configured time window; and
- share at least one meaningful term with the cluster text, when terms are available.

The script reports these as **candidate evidence**, not as proven causes. A change ID can
only appear in output if it came from `data/changes.json`.

### 4. Assign a grounding state

| State | Category score | Permitted conclusion | Route |
|---|---:|---|---|
| `KNOWN` | `>= 0.60` | describe the cluster and reference ranked evidence | playbook/automation may be considered separately |
| `KNOWN-VARIANT` | `0.30–0.59` | describe the pattern, but do not present a known cause as certain | human review |
| `UNKNOWN` | `< 0.30` | describe tickets only; no cause claim | human expert, always |

The script hard-caps confidence for `UNKNOWN` at `0.30`. Confidence is derived from
category match, evidence strength, and cluster size; it is never supplied by a model.

## What makes the output grounded

Every cluster includes an `evidence` object containing:

- `ticket_ids`: source ticket IDs in the cluster;
- `systems`, `regions`, `date_range`: values observed in those tickets;
- `matched_terms`: terms actually found in ticket text;
- `candidate_changes`: real change records with IDs, dates, and matching reasons;
- `cause_claim_allowed`: `false` for unknown clusters;
- `grounding_checks`: counts and lists that can be verified against the input files.

No external retrieval, language-model knowledge, or `_gt_theme` field is needed. A future
LLM may turn this evidence pack into prose, but a validator must reject any entity that is
not present in the pack. If validation fails, show the deterministic summary and route to a
human instead.

## Run it

From the repository root:

```bash
python scripts/grounded_cluster.py \
  --tickets data/tickets.json \
  --changes data/changes.json \
  --out data/grounded_clusters.json
```

The command prints cluster counts and writes JSON suitable for inspection or a UI. The
same command can be run against any of the ten scenario datasets by changing `--tickets`.

## Limits and next controls

This is a deterministic grounding baseline, not a claim that text similarity proves root
cause. Time correlation is evidence for investigation, not causation. Production use
should add schema validation, a human-reviewed category catalog, and a post-generation
entity validator for any LLM narrative.