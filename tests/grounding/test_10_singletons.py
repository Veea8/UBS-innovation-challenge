import unittest

from test_support import assert_grounding_invariants, load_scenario_tickets, run_scenario


class SingletonScenario(unittest.TestCase):
    def test_singleton_heavy_data_is_not_forced_into_one_cluster(self):
        output = run_scenario("scenario_10_singletons.json")
        assert_grounding_invariants(self, output, len(load_scenario_tickets("scenario_10_singletons.json")))
        self.assertGreaterEqual(len(output["clusters"]), 3)
        self.assertLess(max(len(cluster["evidence"]["ticket_ids"]) for cluster in output["clusters"]), 15)


if __name__ == "__main__":
    unittest.main()
