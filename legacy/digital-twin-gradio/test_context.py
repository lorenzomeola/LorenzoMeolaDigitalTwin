import unittest
import sys
from types import ModuleType, SimpleNamespace

pypdf_stub = ModuleType("pypdf")
pypdf_stub.PdfReader = lambda _: SimpleNamespace(pages=[])
sys.modules.setdefault("pypdf", pypdf_stub)

import context


class TwinProjectContextTests(unittest.TestCase):
    def test_prompt_includes_all_three_projects(self):
        prompt = context.TWIN_SYSTEM_PROMPT

        self.assertIn("CCA Fleet Analytics & Predictive Maintenance", prompt)
        self.assertIn("AI Assets Directory", prompt)
        self.assertIn("MatchKeeper", prompt)

    def test_prompt_preserves_project_claims_and_privacy_limits(self):
        prompt = context.TWIN_SYSTEM_PROMPT

        self.assertIn("No Volvo data, screenshots, or internal links", prompt)
        self.assertIn("Stripe Connect", prompt)
        self.assertIn("no validated business impact", prompt.lower())


if __name__ == "__main__":
    unittest.main()
