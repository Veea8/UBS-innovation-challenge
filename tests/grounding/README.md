# Grounding scenario tests

This folder contains one test script for each grounding scenario in `data/`. The tests call `scripts/grounded_cluster.py` as a Python module and check both clustering behavior and the closed-world safety contract.

## Run all tests

From the repository root:

```bash
python -m unittest discover -s tests/grounding -p 'test_*.py' -v
```

## What every test checks

The shared checks verify that:

- every input ticket is represented exactly once;
- `_gt_theme` and other underscore-prefixed fields do not influence processing;
- external sources are not used;
- ticket IDs and candidate change IDs are evidence-shaped and verified;
- unknown clusters are capped at `0.30` confidence;
- unknown clusters cannot make causal claims and route to a human expert.

Scenario-specific checks then verify the expected category, state, evidence, or abstention behavior.

See [GROUNDING_TEST_REPORT.md](GROUNDING_TEST_REPORT.md) for the test setting and observed result for every scenario.
