import unittest

from test_support import assert_grounding_invariants, clusters_by_name, load_scenario_tickets, run_scenario


class PasswordResetScenario(unittest.TestCase):
    def test_background_password_reset_is_not_marked_unknown(self):
        output = run_scenario("scenario_04_password_reset.json")
        assert_grounding_invariants(self, output, len(load_scenario_tickets("scenario_04_password_reset.json")))
        cluster = clusters_by_name(output)["password_reset"]
        self.assertIn(cluster["state"], {"KNOWN", "KNOWN-VARIANT"})
        self.assertNotEqual(cluster["route"], "human_expert")


if __name__ == "__main__":
    unittest.main()
