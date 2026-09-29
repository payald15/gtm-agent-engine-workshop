import importlib
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ["LANGSMITH_TRACING"] = "false"

agent = importlib.import_module("gtm_agent.gtm_agent")
data_service = importlib.import_module("gtm_agent.data_service")


SENSITIVE_FIELDS = {
    "billing_qualification",
    "tax_id",
    "date_of_birth",
    "card_on_file",
    "credit_check_ref",
}


class ProspectPrivacyTests(unittest.TestCase):
    def setUp(self):
        data_service._PROFILES.clear()

    def test_prospect_tools_exclude_billing_data(self):
        contact_result = agent.get_prospect.invoke({"prospect_id": "LEAD-12853"})
        profile_result = agent.build_prospect_profile.invoke({"prospect_id": "LEAD-12853"})

        contact = contact_result["prospect"]
        profile = profile_result["prospect_profile"]
        self.assertTrue(SENSITIVE_FIELDS.isdisjoint(contact))
        self.assertTrue(SENSITIVE_FIELDS.isdisjoint(profile))
        self.assertIn("annual_revenue", profile)
        self.assertIn("tech_stack", profile)

    def test_score_prospect_accepts_reduced_profile(self):
        class FakeResult:
            def model_dump(self):
                return {"score": 85, "justification": "Good fit"}

        class FakeScoringModel:
            def __init__(self):
                self.messages = None

            def invoke(self, messages):
                self.messages = messages
                return FakeResult()

        fake_model = FakeScoringModel()
        profile = agent.build_prospect_profile.invoke({"prospect_id": "LEAD-12853"})[
            "prospect_profile"
        ]
        offering = {
            "required_tech_stack": ["Snowflake"],
            "min_annual_revenue": 1,
            "description": "Data platform",
        }

        with patch.object(agent, "_scoring_llm", fake_model):
            result = agent.score_prospect.invoke(
                {"prospect_profile": profile, "offering": offering}
            )

        self.assertEqual(result["score"], 85)
        messages = fake_model.messages[1]["content"]
        self.assertNotIn("billing_qualification", messages)
        self.assertIn("annual_revenue", messages)
        self.assertIn("tech_stack", messages)
