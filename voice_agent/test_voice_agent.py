"""
Unit & Integration Tests for the Voice Intake Agent & Clinical Triage Engine.
"""

import unittest
import sqlite3
from voice_agent.telephony_voice import (
    VoiceAgentEngine,
    ClinicalSafetyTriager,
    CallIntent,
    TriageLevel
)


class TestVoiceAgent(unittest.TestCase):

    def setUp(self):
        self.engine = VoiceAgentEngine(db_path=":memory:")
        self.test_call_sid = "CA_TEST_12345"
        self.caller_phone = "+12065550199"
        self.practice_id = "PR-001"
        self.practice_name = "Bellevue Aesthetic Medicine"

    def test_emergency_triage_clinical_safety(self):
        """Verify DOC-AA-01 enforcement: emergency red-flag triggers immediate 911 alert."""
        # 1. Severe bleeding
        res = ClinicalSafetyTriager.evaluate("I'm bleeding heavily from my gums after the surgery and it won't stop")
        self.assertTrue(res.is_emergency)
        self.assertEqual(res.triage_level, TriageLevel.EMERGENCY)
        self.assertEqual(res.action, "DISPATCH_911")
        self.assertIn("911", res.safety_message)

        # 2. Breathing difficulty / airway compromise
        res2 = ClinicalSafetyTriager.evaluate("My throat is closing up and I can't breathe after my injection")
        self.assertTrue(res2.is_emergency)
        self.assertEqual(res2.action, "DISPATCH_911")

        # 3. Vascular occlusion indicator (filler emergency)
        res3 = ClinicalSafetyTriager.evaluate("The skin on my nose turned white and I have severe pain after filler")
        self.assertTrue(res3.is_emergency)
        self.assertEqual(res3.action, "DISPATCH_911")

        # 4. Routine inquiry (should NOT trigger emergency)
        res4 = ClinicalSafetyTriager.evaluate("I need to cancel my Morpheus8 appointment tomorrow afternoon")
        self.assertFalse(res4.is_emergency)
        self.assertEqual(res4.triage_level, TriageLevel.ROUTINE)
        self.assertEqual(res4.action, "CONTINUE")

    def test_inbound_greeting_twiml(self):
        twiml = self.engine.start_call(
            self.test_call_sid,
            self.caller_phone,
            self.practice_id,
            self.practice_name
        )
        self.assertIn("<Response>", twiml)
        self.assertIn("<Gather", twiml)
        self.assertIn("Polly.Joanna-Neural", twiml)
        self.assertIn(self.practice_name, twiml)
        self.assertIn("911", twiml)
        self.assertIn(self.test_call_sid, twiml)

    def test_cancellation_intent_and_db_staging(self):
        self.engine.start_call(
            self.test_call_sid,
            self.caller_phone,
            self.practice_id,
            self.practice_name
        )
        intent, spoken, twiml = self.engine.process_utterance(
            self.test_call_sid,
            "Hi, I won't be able to come to my Morpheus appointment tomorrow morning, please cancel it."
        )
        self.assertEqual(intent, CallIntent.CANCEL_APPOINTMENT)
        self.assertIn("registered your cancellation", spoken)
        self.assertIn("<Response>", twiml)

        # Verify record in database
        cursor = self.engine.conn.cursor()
        cursor.execute("SELECT caller_phone, waitlist_triggered FROM appointment_cancellations WHERE call_sid = ?", (self.test_call_sid,))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], self.caller_phone)
        self.assertEqual(row[1], 1)

    def test_consultation_intent_staging(self):
        self.engine.start_call(
            self.test_call_sid,
            self.caller_phone,
            self.practice_id,
            self.practice_name
        )
        intent, spoken, twiml = self.engine.process_utterance(
            self.test_call_sid,
            "I'd like to book a consultation for Botox and cheek fillers next week"
        )
        self.assertEqual(intent, CallIntent.BOOK_CONSULTATION)
        self.assertIn("staged your consultation request", spoken)

        # Verify staged note in database
        cursor = self.engine.conn.cursor()
        cursor.execute("SELECT status, procedure_requested FROM agent_staged_notes WHERE call_sid = ?", (self.test_call_sid,))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "PENDING_STAFF_REVIEW")

    def test_faq_intent(self):
        self.engine.start_call(
            self.test_call_sid,
            self.caller_phone,
            self.practice_id,
            self.practice_name
        )
        intent, spoken, twiml = self.engine.process_utterance(
            self.test_call_sid,
            "What are your office hours and where do I park?"
        )
        self.assertEqual(intent, CallIntent.PRACTICE_FAQ)
        self.assertIn("validated parking", spoken)
        self.assertIn("<Gather", twiml)


if __name__ == "__main__":
    unittest.main()
