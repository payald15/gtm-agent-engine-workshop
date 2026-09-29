import os
import unittest
from types import SimpleNamespace

os.environ["LANGSMITH_TRACING"] = "false"

from gtm_agent.gtm_agent import send_prospect_email


class SendProspectEmailTests(unittest.TestCase):
    def test_blocks_disqualified_prospect(self):
        result = send_prospect_email.func(
            {"prospect_id": "LEAD-50001", "email": "priya.nair@example.com"},
            "A note",
            "Hello",
            SimpleNamespace(config={}),
            from_rep={},
        )

        self.assertEqual(result["status"], "blocked")

    def test_sends_non_disqualified_prospect(self):
        result = send_prospect_email.func(
            {"prospect_id": "LEAD-12853", "email": "omar.okafor@lakesideanalytics.com"},
            "A note",
            "Hello",
            SimpleNamespace(config={}),
            from_rep={},
        )

        self.assertEqual(result["status"], "sent")


if __name__ == "__main__":
    unittest.main()
