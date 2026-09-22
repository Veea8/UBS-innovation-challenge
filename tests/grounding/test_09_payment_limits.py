import unittest

from test_support import assert_grounding_invariants, clusters_by_name, load_scenario_tickets, run_scenario


class PaymentLimitsScenario(unittest.TestCase):
    def test_payment_limits_does_not_absorb_iban_language(self):
        output = run_scenario("scenario_09_payment_limits.json")
        assert_grounding_invariants(self, output, len(load_scenario_tickets("scenario_09_payment_limits.json")))
        cluster = clusters_by_name(output)["payment_limits"]
        self.assertIn(cluster["state"], {"KNOWN", "KNOWN-VARIANT"})
        self.assertNotIn("iban", cluster["evidence"]["matched_terms"])


if __name__ == "__main__":
    unittest.main()
