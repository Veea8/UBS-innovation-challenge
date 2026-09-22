import unittest

from test_support import assert_grounding_invariants, clusters_by_name, load_scenario_tickets, run_scenario


class StatementDownloadScenario(unittest.TestCase):
    def test_statement_download_is_known(self):
        output = run_scenario("scenario_05_statement_download.json")
        assert_grounding_invariants(self, output, len(load_scenario_tickets("scenario_05_statement_download.json")))
        cluster = clusters_by_name(output)["statement_download"]
        self.assertEqual(cluster["state"], "KNOWN")
        self.assertTrue(cluster["cause_claim_allowed"])


if __name__ == "__main__":
    unittest.main()
