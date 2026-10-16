import os
import sys
import unittest
from types import ModuleType
from unittest.mock import Mock, patch

supabase_stub = ModuleType("supabase")
supabase_stub.create_client = lambda *_: None
sys.modules.setdefault("supabase", supabase_stub)

dotenv_stub = ModuleType("dotenv")
dotenv_stub.load_dotenv = lambda **_kwargs: None
sys.modules.setdefault("dotenv", dotenv_stub)

import tools


class ContactToolTests(unittest.TestCase):
    def test_saves_contact_to_the_digital_twin_table(self):
        client = Mock()
        table = client.table.return_value
        table.insert.return_value.execute.return_value.data = [{"id": 1}]

        with (
            patch.dict(
                os.environ,
                {
                    "SUPABASE_URL": "https://example.supabase.co",
                    "SUPABASE_SERVICE_ROLE_KEY": "test-key",
                },
            ),
            patch("tools.create_client", return_value=client),
        ):
            result = tools.record_user_details(
                email="candidate@example.com",
                name="Candidate",
                notes="Interested in an AI Engineer role",
                consent_confirmed=True,
            )

        self.assertEqual(result, {"status": "saved"})
        client.table.assert_called_once_with("twin_contact_requests")
        inserted_contact = table.insert.call_args.args[0]
        self.assertEqual(
            {key: inserted_contact[key] for key in ("email", "name", "notes")},
            {
                "email": "candidate@example.com",
                "name": "Candidate",
                "notes": "Interested in an AI Engineer role",
            },
        )
        self.assertIn("consent_confirmed_at", inserted_contact)

    def test_rejects_contact_storage_without_explicit_consent(self):
        with self.assertRaises(ValueError):
            tools.record_user_details(
                email="candidate@example.com",
                consent_confirmed=False,
            )


if __name__ == "__main__":
    unittest.main()