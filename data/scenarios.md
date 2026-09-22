# Data scenarios for grounding validation

This file describes 10 synthetic scenarios that can be used to demonstrate that the clustering and root-cause workflow is grounded, explainable, and resilient to novelty.

## Scenario 1 — Known category, strong signal

- Theme: mobile login failures after app update
- Expected pattern: tight spike after deployment, clear grouping by system and region
- Grounding goal: the model should identify the cluster and cite only the matching tickets and release change
- Success criterion: high confidence, clear evidence, no invented entities

## Scenario 2 — Known category, recurring theme

- Theme: recurring APAC FX settlement mismatch
- Expected pattern: repeated episodes across several days with similar closure notes
- Grounding goal: the model should treat the issue as recurring and grounded in the ticket text, not as a one-off
- Success criterion: clear evidence chain to the recurrent time pattern and vendor feed change

## Scenario 3 — Unknown category, low-volume novelty

- Theme: Austrian IBAN validation regression
- Expected pattern: low volume, spread across dates, varied wording
- Grounding goal: the model should avoid guessing a cause when no category or playbook exists
- Success criterion: cluster identified, cause withheld, human review required

## Scenario 4 — Flat background noise

- Theme: password reset / locked account flow
- Expected pattern: steady background volume without major spikes
- Grounding goal: the model should group the cluster without misreading it as an incident
- Success criterion: correct category mapping, supported by frequent repeated keywords and known workflow

## Scenario 5 — Slow-burn operational degradation

- Theme: month-end reporting latency
- Expected pattern: recurring bumps around reporting cycles
- Grounding goal: the model should identify a slow-burn pattern not a release-induced outage
- Success criterion: explanation tied to dates and report timing rather than unrelated deploy logs

## Scenario 6 — Geography-sensitive cluster

- Theme: card blocked abroad
- Expected pattern: travel-related clusters with strong regional skew and seasonal travel behavior
- Grounding goal: the model should not over-attribute to a single system or region absent from the evidence
- Success criterion: correct cluster boundaries and grounded region notes

## Scenario 7 — Mixed system spillover

- Theme: mobile login issues spilling to eBanking
- Expected pattern: same client experience reflected across two systems
- Grounding goal: demonstrate that blast radius is supported by overlapping symptoms and not just by a single ticket
- Success criterion: correct explanation using evidence from both systems without fabricating a root cause

## Scenario 8 — Singleton-heavy case

- Theme: one-off support / non-incident tickets
- Expected pattern: many singletons with no real cluster
- Grounding goal: the system should not force every ticket into a theme
- Success criterion: the clusterer should identify low-confidence, non-incident behavior and preserve singleton separation

## Scenario 9 — Decoy-heavy change environment

- Theme: innocent deploys around a real incident
- Expected pattern: several nearby, unrelated change events around the real cause
- Grounding goal: demonstrate that root-cause ranking must discriminate by system, region, and lag, not just proximity in time
- Success criterion: the correct change wins without relying on a simplistic date-only heuristic

## Scenario 10 — Low-confidence / insufficient evidence

- Theme: borderline or weakly clustered set
- Expected pattern: small cluster, high variance, low keyword consistency
- Grounding goal: the model should abstain when evidence is insufficient
- Success criterion: cluster rendered as descriptive only, no causal claim, low confidence with a human handoff

## Evaluation idea

For each scenario, assess:

1. Was the cluster grounded in the actual ticket text?
2. Did the model name only valid ticket IDs, change IDs, systems, and regions?
3. Did it avoid unsupported root-cause assertions?
4. Did it abstain in novel or weakly grounded situations?
5. Did confidence reflect evidence quality and not model certainty alone?

These 10 scenarios give a practical testing suite for demonstrating that the grounding issue has been solved in the clustering workflow.
