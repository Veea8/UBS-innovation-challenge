import unittest

from test_support import assert_grounding_invariants, clusters_by_name, load_scenario_tickets, run_scenario


class KnownLoginScenario(unittest.TestCase):
    def test_known_login_is_clustered_with_real_change_evidence(self):
        output = run_scenario("scenario_01_known_login.json")
        assert_grounding_invariants(self, output, len(load_scenario_tickets("scenario_01_known_login.json")))
        clusters = clusters_by_name(output)
        login = clusters["mobile_login_failure"]
        self.assertGreaterEqual(len(login["evidence"]["ticket_ids"]), 250)
        self.assertIn(login["state"], {"KNOWN", "KNOWN-VARIANT"})
        self.assertTrue(login["evidence"]["candidate_changes"])
        self.assertTrue(login["evidence"]["grounding_checks"]["change_ids_verified"])


if __name__ == "__main__":
    unittest.main()
