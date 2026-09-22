import unittest

from test_support import assert_grounding_invariants, clusters_by_name, load_scenario_tickets, run_scenario


class ReportingScenario(unittest.TestCase):
    def test_reporting_slow_burn_is_a_variant_not_a_fabricated_incident(self):
        output = run_scenario("scenario_07_reporting.json")
        assert_grounding_invariants(self, output, len(load_scenario_tickets("scenario_07_reporting.json")))
        cluster = clusters_by_name(output)["reporting_slow_month_end"]
        self.assertEqual(cluster["state"], "KNOWN-VARIANT")
        self.assertEqual(cluster["route"], "human_review")


if __name__ == "__main__":
    unittest.main()
