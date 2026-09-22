import unittest

from test_support import assert_grounding_invariants, clusters_by_name, load_scenario_tickets, run_scenario


class OnboardingScenario(unittest.TestCase):
    def test_onboarding_upload_uses_observed_vocabulary(self):
        output = run_scenario("scenario_08_onboarding_upload.json")
        assert_grounding_invariants(self, output, len(load_scenario_tickets("scenario_08_onboarding_upload.json")))
        cluster = clusters_by_name(output)["onboarding_upload"]
        self.assertIn("upload", cluster["evidence"]["matched_terms"])
        self.assertIn(cluster["state"], {"KNOWN", "KNOWN-VARIANT"})


if __name__ == "__main__":
    unittest.main()
