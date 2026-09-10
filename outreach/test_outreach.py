"""
Unit Tests for the Outreach & Business Development Suite.
"""

import unittest
from outreach.campaign_templates import (
    ProspectProfile,
    CampaignTemplateEngine,
    generate_prospect_campaign
)
from outreach.prospect_outreach_dossiers import (
    TOP_5_TARGETS,
    generate_all_flagship_dossiers
)


class TestOutreachSuite(unittest.TestCase):

    def setUp(self):
        self.sample_prospect = ProspectProfile(
            prospect_id="PR-TEST",
            practice_name="Olympic Aesthetics",
            specialty="Medical Spa",
            location="Seattle, WA",
            decision_maker="Dr. Jane Smith",
            decision_maker_title="Medical Director",
            email="dr.smith@olympiaesthetics.com",
            phone="(206) 555-9999",
            booking_url="https://olympiaesthetics.com/schedule",
            current_pms="Boulevard",
            trackers_detected=["Meta (Facebook) Pixel", "TikTok Pixel"],
            risk_rating="CRITICAL",
            est_annual_revenue="$2,500,000",
            flagship_procedure="Morpheus8",
            est_cancellation_loss="$1,200",
            dormant_credits_est="$24,000",
            scorecard_filename="prospects/scorecards/PR-TEST_olympic_scorecard.html"
        )

    def test_sequence_generation(self):
        seq = CampaignTemplateEngine.generate_sequence(self.sample_prospect)
        self.assertEqual(len(seq.touches), 6)
        
        # Verify Touch 1 (Compliance Wedge)
        t1 = seq.touches[0]
        self.assertEqual(t1.channel, "Email")
        self.assertEqual(t1.day_offset, 1)
        self.assertIn("vulnerability detected", t1.subject)
        self.assertIn("FTC Health Breach Notification Rule", t1.content)
        self.assertIn("PR-TEST_olympic_scorecard.html", t1.content)

        # Verify Touch 2 (Operational ROI)
        t2 = seq.touches[1]
        self.assertEqual(t2.day_offset, 4)
        self.assertIn("Morpheus8 cancellations", t2.subject)
        self.assertIn("$1,200", t2.content)
        self.assertIn("$24,000", t2.content)

        # Verify Touch 3 (Founding Partner Guarantee)
        t3 = seq.touches[2]
        self.assertEqual(t3.day_offset, 8)
        self.assertIn("30-day milestone guarantee", t3.subject)
        self.assertIn("30-Day Milestone Guarantee", t3.content)
        self.assertIn("(206) 880-0477", t3.content)

        # Verify LinkedIn Connection Note length <= 300 chars
        li_connect = seq.touches[3]
        self.assertLessEqual(len(li_connect.content), 300)

    def test_flagship_dossiers_compilation(self):
        self.assertEqual(len(TOP_5_TARGETS), 5)
        dossiers_md = generate_all_flagship_dossiers()
        self.assertIn("Luxe Aesthetics Group", dossiers_md)
        self.assertIn("Bellevue Aesthetic Medicine", dossiers_md)
        self.assertIn("Lake Washington Facial Plastic Surgery", dossiers_md)
        self.assertIn("Seattle Cosmetic Dentistry", dossiers_md)
        self.assertIn("Cascadia Med Spa", dossiers_md)
        self.assertGreater(len(dossiers_md), 5000)


if __name__ == "__main__":
    unittest.main()
