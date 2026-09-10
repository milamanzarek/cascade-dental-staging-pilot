"""
Unit Tests for the Windows Clinic Edge Installer & Config Wizard.
"""

import os
import tempfile
import unittest
from installer.config_wizard import (
    ClinicConfig,
    PMSType,
    CarrierType,
    ConfigWizardEngine,
    run_preflight_checks
)


class TestInstaller(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_clinic_config_validation(self):
        valid_config = ClinicConfig(
            clinic_id="PR-001",
            clinic_name="Bellevue Aesthetic Medicine",
            pms_type=PMSType.BOULEVARD,
            db_path="data/clinic.db",
            gateway_url="wss://gateway.lane3healthcare.com/ws/edge",
            api_token="super_secret_auth_token_12345"
        )
        is_valid, errors = valid_config.validate()
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

        # Invalid: missing token and non-TLS gateway
        invalid_config = ClinicConfig(
            clinic_id="P",
            clinic_name="",
            pms_type=PMSType.OPEN_DENTAL,
            db_path="",
            gateway_url="http://insecure.gateway.com",
            api_token="short"
        )
        is_valid_inv, errors_inv = invalid_config.validate()
        self.assertFalse(is_valid_inv)
        self.assertGreaterEqual(len(errors_inv), 3)

    def test_config_generation_and_export(self):
        config = ClinicConfig(
            clinic_id="PR-021",
            clinic_name="Luxe Aesthetics Group",
            pms_type=PMSType.ZENOTI,
            db_path="https://api.zenoti.com/v1",
            gateway_url="wss://gateway.lane3healthcare.com/ws/edge",
            api_token="zenoti_auth_bearer_998877"
        )
        env_file = ConfigWizardEngine.generate_and_save(config, self.temp_dir.name)
        self.assertTrue(os.path.exists(env_file))

        with open(env_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("LANE3_CLINIC_ID=PR-021", content)
        self.assertIn("LANE3_CLINIC_NAME=Luxe Aesthetics Group", content)
        self.assertIn("LANE3_PMS_TYPE=zenoti", content)
        self.assertIn("LANE3_ZERO_PORT_TUNNEL=true", content)
        self.assertIn("LANE3_PHI_SANITIZER=true", content)

        # Verify redacted json config exists
        json_file = os.path.join(self.temp_dir.name, "clinic_config.json")
        self.assertTrue(os.path.exists(json_file))
        with open(json_file, "r", encoding="utf-8") as f:
            json_content = f.read()
        self.assertNotIn("zenoti_auth_bearer_998877", json_content)  # Token must be redacted
        self.assertIn("...", json_content)

    def test_powershell_script_syntax_and_integrity(self):
        ps1_path = os.path.join(os.path.dirname(__file__), "install_lane3_daemon.ps1")
        self.assertTrue(os.path.exists(ps1_path))
        with open(ps1_path, "r", encoding="utf-8") as f:
            ps1_text = f.read()
        self.assertIn("Lane 3 Healthcare AI", ps1_text)
        self.assertIn("New-ScheduledTaskAction", ps1_text)
        self.assertIn("LANE3_ZERO_PORT_TUNNEL=true", ps1_text)
        self.assertIn("Zero-Port Architecture", ps1_text)


if __name__ == "__main__":
    unittest.main()
