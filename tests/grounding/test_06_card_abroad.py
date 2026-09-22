import unittest

from test_support import assert_grounding_invariants, clusters_by_name, load_scenario_tickets, run_scenario


class CardAbroadScenario(unittest.TestCase):
    def test_card_abroad_preserves_system_and_region_evidence(self):
        output = run_scenario("scenario_06_card_abroad.json")
        assert_grounding_invariants(self, output, len(load_scenario_tickets("scenario_06_card_abroad.json")))
        cluster = clusters_by_name(output)["card_blocked_abroad"]
        self.assertEqual(cluster["state"], "KNOWN")
        self.assertEqual(cluster["evidence"]["systems"], ["CardServices"])
        self.assertTrue(cluster["evidence"]["regions"])


if __name__ == "__main__":
    unittest.main()
