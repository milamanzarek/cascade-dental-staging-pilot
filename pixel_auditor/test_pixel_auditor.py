"""
Unit & Integration Test Suite for Pixel Auditor.

Verifies:
1. Detection of Meta Pixel inline initialization (fbq).
2. Detection of Google Analytics 4 (GA4) measurement IDs.
3. Extraction of exfiltrated clinical terms from URL parameters (?service=botox).
4. Identification of booking iframes (Boulevard, Zenoti, NexHealth).
5. Clean verification of 100% compliant zero-telemetry pages.
6. Scorecard HTML generation.
"""

import asyncio
import unittest
from pixel_auditor.auditor import PixelAuditor
from pixel_auditor.scorecard_generator import ScorecardGenerator


class TestPixelAuditor(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.auditor = PixelAuditor("https://example-medspa.com/book")

    async def test_01_detects_non_compliant_medspa_page(self):
        """Verify detector catches Meta Pixel, GA4, and Botox clinical term in non-compliant HTML."""
        dirty_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://connect.facebook.net/en_US/fbevents.js"></script>
            <script>
                fbq('init', '1092837465');
                fbq('track', 'PageView');
            </script>
            <script async src="https://www.googletagmanager.com/gtag/js?id=G-XYZ123"></script>
        </head>
        <body>
            <h1>Book Your Botox & Filler Treatment</h1>
            <iframe src="https://joinblvd.com/booking/widget"></iframe>
        </body>
        </html>
        """
        results = await self.auditor.audit_html_content(
            dirty_html,
            base_url="https://example-medspa.com/book?service=botox&provider=drvance"
        )
        self.assertEqual(results["hard_gate_verdict"], "FAIL (U-HG-02 Violation)")
        self.assertEqual(results["risk_rating"], "CRITICAL")
        self.assertGreaterEqual(results["total_violations"], 2)

        # Check detected clinical terms
        all_detected_terms = []
        for v in results["violations"]:
            all_detected_terms.extend(v.get("detected_clinical_terms", []))
        self.assertIn("botox", all_detected_terms)

        # Check detected iframe
        self.assertEqual(len(results["detected_iframes"]), 1)
        self.assertEqual(results["detected_iframes"][0]["vendor"], "Boulevard Online Booking")

    async def test_02_passes_clean_zero_telemetry_page(self):
        """Verify detector passes a 100% clean Open Dental / Lane 3 booking page."""
        clean_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Cascade Dental Arts - Schedule Appointment</title>
            <link rel="stylesheet" href="/styles.css">
        </head>
        <body>
            <h1>Select an Appointment Slot</h1>
            <form action="/claim" method="POST">
                <input type="hidden" name="token" value="8f7a2b">
                <button type="submit">Confirm Appointment</button>
            </form>
        </body>
        </html>
        """
        results = await self.auditor.audit_html_content(clean_html, base_url="https://cascadedental.app/s/8f7a2b")
        self.assertEqual(results["hard_gate_verdict"], "PASS (U-HG-02 Compliant)")
        self.assertEqual(results["risk_rating"], "LOW")
        self.assertEqual(results["total_violations"], 0)
        self.assertEqual(results["statutory_daily_exposure"], 0)

    def test_03_scorecard_html_generation(self):
        """Verify scorecard generator produces valid HTML with critical alerts."""
        mock_data = {
            "target_url": "https://luxury-aesthetic-clinic.com/schedule",
            "hard_gate_verdict": "FAIL (U-HG-02 Violation)",
            "risk_rating": "CRITICAL",
            "total_violations": 2,
            "statutory_daily_exposure": 50120,
            "violations": [
                {
                    "tracker": "Meta (Facebook) Pixel",
                    "host": "connect.facebook.net",
                    "severity": "CRITICAL",
                    "url": "https://connect.facebook.net/en_US/fbevents.js",
                    "detected_clinical_terms": ["botox"]
                }
            ]
        }
        html = ScorecardGenerator.generate_html(mock_data)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("CRITICAL RISK RATING", html)
        self.assertIn("$50,120", html)
        self.assertIn("Meta (Facebook) Pixel", html)
        self.assertIn("PHI Exfiltration: botox", html)


if __name__ == "__main__":
    unittest.main()
