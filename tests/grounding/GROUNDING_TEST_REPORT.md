# Grounding test report

## Purpose

This suite tests whether the deterministic clusterer can find useful patterns while staying inside the supplied evidence. It uses the ten JSON datasets in `data/` and the shared `data/changes.json` change log.

The tests do not treat `_gt_theme` as input. They check the output contract instead: source ticket coverage, valid evidence identifiers, no external sources, no ground-truth use, and safe routing for unknown cases.

## Scenario results

| Test | Problem setting | Expected behavior | Observed outcome |
|---|---|---|---|
| 01 known login | High-volume MobileApp login failures after an update | Match login vocabulary and identify real nearby change evidence | **Pass**: `mobile_login_failure`, 255 tickets, `KNOWN-VARIANT`, candidate changes present |
| 02 FX recurrence | Repeated APAC FX settlement mismatch | Recognize known FX pattern; do not invent a change when textual overlap is insufficient | **Pass**: `fx_settlement`, 42 tickets, `KNOWN`, `evidence_review`, no unsupported change candidate |
| 03 unknown IBAN | Austrian IBAN validation issue with no approved category | Cluster descriptively, withhold cause, escalate | **Pass**: `unclassified`, 11 tickets, `UNKNOWN`, confidence `<= 0.30`, `human_expert` |
| 04 password reset | Routine background password-reset traffic | Recognize known workflow without treating it as unseen | **Pass**: `password_reset`, 230 tickets, `KNOWN-VARIANT` |
| 05 statement download | Known eBanking statement-download workflow | Match known category | **Pass**: `statement_download`, 150 tickets, `KNOWN` |
| 06 card abroad | Region-sensitive card failures while travelling | Preserve system and observed region evidence | **Pass**: `card_blocked_abroad`, 140 tickets, `KNOWN` |
| 07 reporting | Slow-burn month-end reporting degradation | Treat partial match as reviewable variant | **Pass**: `reporting_slow_month_end`, 120 tickets, `KNOWN-VARIANT`, `human_review` |
| 08 onboarding | Document upload and validation failures | Use observed upload vocabulary and controlled category | **Pass**: `onboarding_upload`, 110 tickets, `KNOWN-VARIANT` |
| 09 payment limits | Known payment-limit workflow | Match payment vocabulary without absorbing IBAN terms | **Pass**: `payment_limits`, 130 tickets, `KNOWN-VARIANT`; `iban` excluded |
| 10 singleton-heavy | Small, varied support tickets with weak commonality | Avoid forcing all data into one incident | **Pass**: 6 separate clusters, largest cluster has fewer than 15 tickets |

## Outcome

The suite demonstrates the intended grounding behavior:

- known data can be grouped and linked to real change records;
- partial matches are routed for review rather than silently automated;
- the novel IBAN case is grouped but cannot receive a causal claim;
- weak, mixed data is not collapsed into one fabricated incident;
- every scenario is checked for source-only identifiers and absence of external or ground-truth inputs.

## Important limitation

These tests validate the deterministic evidence boundary. They do not prove causation. If an LLM is added later, its output needs a second validator that checks every ticket ID, change ID, system, region, date, quote, and cause against the evidence pack produced by the script.
