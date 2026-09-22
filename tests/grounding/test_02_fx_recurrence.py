import unittest

from test_support import assert_grounding_invariants, clusters_by_name, load_scenario_tickets, run_scenario


class FxRecurrenceScenario(unittest.TestCase):
    def test_fx_recurrence_remains_known_and_evidence_linked(self):
        output = run_scenario("scenario_02_fx_recurrence.json")
        assert_grounding_invariants(self, output, len(load_scenario_tickets("scenario_02_fx_recurrence.json")))
        cluster = clusters_by_name(output)["fx_settlement"]
        self.assertEqual(cluster["state"], "KNOWN")
        self.assertEqual(cluster["route"], "evidence_review")
        self.assertTrue(cluster["cause_claim_allowed"])
        self.assertTrue(cluster["evidence"]["grounding_checks"]["change_ids_verified"])


if __name__ == "__main__":
    unittest.main()
