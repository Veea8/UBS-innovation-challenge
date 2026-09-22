from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from grounded_cluster import build_output  # noqa: E402


TICKETS = ROOT / "data" / "tickets.json"
CHANGES = ROOT / "data" / "changes.json"


def load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_scenario(filename: str) -> dict[str, Any]:
    tickets = load_json(ROOT / "data" / filename)
    changes = load_json(CHANGES)
    return build_output(tickets, changes, window_days=7)


def clusters_by_name(output: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {cluster["name"]: cluster for cluster in output["clusters"]}


def assert_grounding_invariants(test: unittest.TestCase, output: dict[str, Any], ticket_count: int) -> None:
    test.assertEqual(sum(len(cluster["evidence"]["ticket_ids"]) for cluster in output["clusters"]), ticket_count)
    for cluster in output["clusters"]:
        evidence = cluster["evidence"]
        checks = evidence["grounding_checks"]
        test.assertFalse(checks["external_sources_used"])
        test.assertFalse(checks["ground_truth_fields_used"])
        test.assertTrue(checks["ticket_ids_verified"])
        test.assertTrue(checks["change_ids_verified"])
        test.assertTrue(0.0 <= cluster["confidence"] <= 1.0)
        if cluster["state"] == "UNKNOWN":
            test.assertLessEqual(cluster["confidence"], 0.30)
            test.assertFalse(cluster["cause_claim_allowed"])
            test.assertEqual(cluster["route"], "human_expert")
        for change in evidence["candidate_changes"]:
            test.assertTrue(change["evidence_only"])
            test.assertRegex(change["change_id"], r"^CHG-\d{4}$")


def load_scenario_tickets(filename: str) -> list[dict[str, Any]]:
    return load_json(ROOT / "data" / filename)
