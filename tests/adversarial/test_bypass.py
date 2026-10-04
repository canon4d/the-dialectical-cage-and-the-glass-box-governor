import unittest

from evaluation.bypass import probe


class DirectBypass(unittest.TestCase):
    def test_complete_mediation_is_reported_as_not_established(self):
        r = probe()
        self.assertEqual(r["classification"], "COMPLETE_MEDIATION_NOT_ESTABLISHED")

    def test_out_of_band_change_is_detected_on_next_mediated_request(self):
        r = probe()
        self.assertEqual(r["mediated_request_after_bypass"],
                         {"decision": "BLOCK", "reason": "STATE_INCONSISTENT"})


if __name__ == "__main__":
    unittest.main()
