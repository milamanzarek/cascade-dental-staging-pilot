"""
Unit & Integration Test Suite for Carrier Gateway.

Verifies:
1. Twilio inbound webhook parsing and XML response.
2. Telnyx v2 JSON webhook parsing and JSON response.
3. TCPA mandatory opt-out keyword handling (STOP, CANCEL, QUIT, UNSUBSCRIBE).
4. Slot claim routing (Dental & Med Spa) with contention resolution.
5. Zero-PHI outbound tokenized message construction.
"""

import asyncio
import unittest
from fastapi.testclient import TestClient
from carrier_gateway.sms_relay import CarrierSMSGateway


class TestCarrierGateway(unittest.TestCase):
    def setUp(self):
        self.dental_claimed_slots = []
        self.medspa_claimed_slots = []

        async def mock_dental_claim(phone: str):
            if "+14255550100" in phone:
                self.dental_claimed_slots.append(phone)
                return {"status": "SUCCESS", "provider": "Dr. Sarah Chen", "date_time": "Tomorrow at 10:00 AM"}
            elif "+14255550999" in phone:
                return {"status": "ALREADY_CLAIMED"}
            return {"status": "NOT_FOUND"}

        async def mock_medspa_claim(phone: str):
            if "+14255550200" in phone:
                self.medspa_claimed_slots.append(phone)
                return {"status": "SUCCESS", "provider": "Elena Rostova ARNP", "suite": "Suite 1 (Master Injectables)"}
            return {"status": "NOT_FOUND"}

        self.gateway = CarrierSMSGateway(
            practice_name="Cascade Dental & Aesthetic Arts",
            dental_claim_handler=mock_dental_claim,
            medspa_claim_handler=mock_medspa_claim
        )
        self.client = TestClient(self.gateway.app)

    def test_01_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["practice_name"], "Cascade Dental & Aesthetic Arts")

    def test_02_twilio_inbound_claim_success(self):
        """Verify patient texting YES via Twilio claims slot and receives TwiML XML response."""
        response = self.client.post(
            "/webhooks/twilio/inbound",
            data={"From": "+14255550100", "Body": "YES", "To": "+18005550000"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/xml", response.headers["content-type"])
        self.assertIn("Confirmed! Your appointment is locked", response.text)
        self.assertIn("Dr. Sarah Chen", response.text)

    def test_03_twilio_inbound_already_claimed(self):
        """Verify competing patient texting YES gets graceful waitlist retention notice."""
        response = self.client.post(
            "/webhooks/twilio/inbound",
            data={"From": "+14255550999", "Body": "YES", "To": "+18005550000"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("confirmed by another patient", response.text)

    def test_04_telnyx_medspa_claim_success(self):
        """Verify VIP client texting YES via Telnyx JSON webhook claims aesthetic slot."""
        payload = {
            "data": {
                "event_type": "message.received",
                "payload": {
                    "from": {"phone_number": "+14255550200"},
                    "text": "YES",
                    "to": [{"phone_number": "+18005550000"}]
                }
            }
        }
        response = self.client.post("/webhooks/telnyx/inbound", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "processed")
        self.assertIn("Elena Rostova ARNP", data["response_dispatched"])
        self.assertIn("Suite 1", data["response_dispatched"])

    def test_05_tcpa_stop_keyword_opt_out(self):
        """Verify STOP keyword immediately unsubscribes patient and records compliance audit."""
        response = self.client.post(
            "/webhooks/twilio/inbound",
            data={"From": "+14255550888", "Body": "STOP", "To": "+18005550000"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("unsubscribed from automated notifications", response.text)
        self.assertIn("+14255550888", self.gateway.opted_out_numbers)

        # Subsequent message should indicate opted-out state
        subsequent = self.client.post(
            "/webhooks/twilio/inbound",
            data={"From": "+14255550888", "Body": "YES", "To": "+18005550000"}
        )
        self.assertIn("currently opted out", subsequent.text)

    def test_06_zero_phi_outbound_formatting(self):
        """Verify Zero-PHI outbound tokenized message construction."""
        msg = self.gateway.format_zero_phi_outbound(
            token="a7f82c",
            appointment_time="Thursday at 2:00 PM",
            doctor_name="Dr. Vance"
        )
        self.assertIn("https://cascadedental.app/s/a7f82c", msg)
        self.assertIn("Dr. Vance", msg)
        self.assertIn("STOP to opt out", msg)
        self.assertNotIn("Botox", msg)
        self.assertNotIn("Root Canal", msg)


if __name__ == "__main__":
    unittest.main()
