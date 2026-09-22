import unittest

from test_support import assert_grounding_invariants, clusters_by_name, load_scenario_tickets, run_scenario


class UnknownIbanScenario(unittest.TestCase):
    def test_unknown_iban_is_described_but_not_given_a_cause(self):
        output = run_scenario("scenario_03_iban_unknown.json")
        assert_grounding_invariants(self, output, len(load_scenario_tickets("scenario_03_iban_unknown.json")))
        cluster = clusters_by_name(output)["unclassified"]
        self.assertEqual(cluster["state"], "UNKNOWN")
        self.assertEqual(cluster["route"], "human_expert")
        self.assertFalse(cluster["cause_claim_allowed"])
        self.assertLessEqual(cluster["confidence"], 0.30)


if __name__ == "__main__":
    unittest.main()
