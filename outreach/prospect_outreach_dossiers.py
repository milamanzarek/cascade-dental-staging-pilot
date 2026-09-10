"""
Top 5 Flagship Prospect Outreach Dossier Generator.

Compiles fully rendered, personalized campaigns for our top 5 priority
acquisition targets from the empirical strike list:
1. PR-021: Luxe Aesthetics Group (Julian Vance / Dr. Marcus Vance)
2. PR-001: Bellevue Aesthetic Medicine & Laser Institute (Dr. Alistair Ross / Jessica Vance)
3. PR-002: Lake Washington Facial Plastic Surgery (Dr. Edward Sterling)
4. PR-012: Seattle Cosmetic Dentistry & Implant Center (Dr. Alexander Wright)
5. PR-005: Cascadia Med Spa & Longevity Hub (Dr. Marcus Vance / Tyler Hayes)
"""

import os
from typing import List, Dict, Any
from .campaign_templates import ProspectProfile, CampaignTemplateEngine, OutreachSequence

TOP_5_TARGETS: List[Dict[str, Any]] = [
    {
        "prospect_id": "PR-021",
        "practice_name": "Luxe Aesthetics Group (3 Locations)",
        "specialty": "Multi-Location Aesthetic MSO",
        "location": "Seattle, Bellevue, Kirkland, WA",
        "decision_maker": "Julian Vance & Dr. Marcus Vance",
        "decision_maker_title": "CEO & Chief Medical Officer",
        "email": "julian@luxeaestheticsgroup.com",
        "phone": "(206) 555-0100",
        "booking_url": "https://luxeaestheticsgroup.com/book-suite?treatment=botox&location=bellevue",
        "current_pms": "Zenoti Enterprise",
        "trackers_detected": [
            "Meta (Facebook) Pixel (connect.facebook.net/en_US/fbevents.js)",
            "TikTok Pixel (analytics.tiktok.com/i18n/pixel/events.js)",
            "Criteo Marketing Tracker (static.criteo.net/js/ld/ld.js)",
            "Google Tag Manager Container (googletagmanager.com/gtm.js)"
        ],
        "risk_rating": "CRITICAL (U-HG-02 Violation)",
        "est_annual_revenue": "$6,800,000",
        "flagship_procedure": "Morpheus8 & Full-Face Voluma",
        "est_cancellation_loss": "$1,450",
        "dormant_credits_est": "$42,600",
        "scorecard_filename": "prospects/scorecards/PR-021_luxe_aesthetics_group_scorecard.html"
    },
    {
        "prospect_id": "PR-001",
        "practice_name": "Bellevue Aesthetic Medicine & Laser Institute",
        "specialty": "High-End Aesthetic Medicine & Lasers",
        "location": "Downtown Bellevue, WA",
        "decision_maker": "Dr. Alistair Ross & Jessica Vance",
        "decision_maker_title": "Medical Director & Practice Director",
        "email": "director@bellevueaestheticmed.com",
        "phone": "(425) 555-0144",
        "booking_url": "https://bellevueaestheticmedicine.com/book?service=morpheus8",
        "current_pms": "Boulevard (Cloud)",
        "trackers_detected": [
            "Meta (Facebook) Pixel (connect.facebook.net/en_US/fbevents.js)",
            "TikTok Pixel (analytics.tiktok.com/i18n/pixel/events.js)",
            "Google Tag Manager Container (googletagmanager.com/gtm.js)"
        ],
        "risk_rating": "CRITICAL (U-HG-02 Violation)",
        "est_annual_revenue": "$2,800,000",
        "flagship_procedure": "Morpheus8 Burst RF & BBL",
        "est_cancellation_loss": "$1,200",
        "dormant_credits_est": "$29,400",
        "scorecard_filename": "prospects/scorecards/PR-001_bellevue_aesthetic_medicine_scorecard.html"
    },
    {
        "prospect_id": "PR-002",
        "practice_name": "Lake Washington Facial Plastic Surgery",
        "specialty": "Facial Plastic Surgery & Injectable Center",
        "location": "Carillon Point, Kirkland, WA",
        "decision_maker": "Dr. Edward Sterling, FACS",
        "decision_maker_title": "Founder & Board-Certified Plastic Surgeon",
        "email": "dr.sterling@lakewashplastics.com",
        "phone": "(425) 555-0188",
        "booking_url": "https://lakewashingtonplastics.com/consultation?procedure=facelift&fillers=true",
        "current_pms": "Zenoti (REST v2)",
        "trackers_detected": [
            "Meta (Facebook) Pixel (connect.facebook.net/en_US/fbevents.js)",
            "Criteo Marketing Tracker (static.criteo.net/js/ld/ld.js)",
            "Google Tag Manager Container (googletagmanager.com/gtm.js)"
        ],
        "risk_rating": "CRITICAL (U-HG-02 Violation)",
        "est_annual_revenue": "$4,200,000",
        "flagship_procedure": "Facelift Consultation & Sculptra",
        "est_cancellation_loss": "$1,500",
        "dormant_credits_est": "$34,200",
        "scorecard_filename": "prospects/scorecards/PR-002_lake_washington_plastics_scorecard.html"
    },
    {
        "prospect_id": "PR-012",
        "practice_name": "Seattle Cosmetic Dentistry & Implant Center",
        "specialty": "Implantology & Full-Arch Restorative Dentistry",
        "location": "Pike Place / Downtown Seattle, WA",
        "decision_maker": "Dr. Alexander Wright, DDS",
        "decision_maker_title": "Managing Partner & Implant Surgeon",
        "email": "dr.wright@seattlecosmeticimplants.com",
        "phone": "(206) 555-0133",
        "booking_url": "https://seattlecosmeticimplants.com/consultation?service=allon4",
        "current_pms": "Open Dental + NexHealth",
        "trackers_detected": [
            "Meta (Facebook) Pixel (connect.facebook.net/en_US/fbevents.js)",
            "TikTok Pixel (analytics.tiktok.com/i18n/pixel/events.js)",
            "Google Tag Manager Container (googletagmanager.com/gtm.js)"
        ],
        "risk_rating": "CRITICAL (U-HG-02 Violation)",
        "est_annual_revenue": "$3,900,000",
        "flagship_procedure": "All-on-4 Full-Arch & Sedation Surgical Slots",
        "est_cancellation_loss": "$2,200",
        "dormant_credits_est": "$16,800",
        "scorecard_filename": "prospects/scorecards/PR-012_seattle_cosmetic_dentistry_scorecard.html"
    },
    {
        "prospect_id": "PR-005",
        "practice_name": "Cascadia Med Spa & Longevity Hub",
        "specialty": "Medical Aesthetics, Weight Loss & Longevity",
        "location": "Redmond, WA",
        "decision_maker": "Dr. Marcus Vance & Tyler Hayes",
        "decision_maker_title": "Co-Founders & Managing Directors",
        "email": "management@cascadiamedspa.com",
        "phone": "(425) 555-0155",
        "booking_url": "https://cascadiamedspa.com/schedule?service=semaglutide&hrt=true",
        "current_pms": "Zenoti (REST v2)",
        "trackers_detected": [
            "Meta (Facebook) Pixel (connect.facebook.net/en_US/fbevents.js)",
            "Google Tag Manager Container (googletagmanager.com/gtm.js)"
        ],
        "risk_rating": "CRITICAL (U-HG-02 Violation)",
        "est_annual_revenue": "$2,200,000",
        "flagship_procedure": "Semaglutide Concierge & Microneedling",
        "est_cancellation_loss": "$950",
        "dormant_credits_est": "$21,500",
        "scorecard_filename": "prospects/scorecards/PR-005_cascadia_medspa_redmond_scorecard.html"
    }
]


def generate_all_flagship_dossiers() -> str:
    """Renders the comprehensive dossier markdown document for all top 5 targets."""
    output_lines = [
        "# Top 5 Flagship Prospect Outreach Dossiers: Tailored Acquisition Sequences",
        "",
        "- **Target Market**: Greater Seattle & Eastside Outpatient Aesthetic & Dental Practices",
        "- **Conversion Wedge**: Empirical Tracking Pixel Audit Scorecards ($50,120/day statutory liability)",
        "- **Value Proposition**: Sub-15ms local cancellation recovery + Beauty Bank dormant balance activation",
        "- **Commercial Terms**: Founding Partner Pilot ($2,000 setup + $450/mo flat retainer + 30-Day Milestone Guarantee)",
        "",
        "---",
        ""
    ]

    for raw in TOP_5_TARGETS:
        profile = ProspectProfile(**raw)
        seq = CampaignTemplateEngine.generate_sequence(profile)
        output_lines.append(seq.to_markdown())
        output_lines.append("\n\n" + "=" * 80 + "\n\n")

    return "\n".join(output_lines)


def export_dossiers_to_file(filepath: str) -> None:
    content = generate_all_flagship_dossiers()
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Exported Flagship Dossiers to {filepath} ({len(content)} bytes)")


if __name__ == "__main__":
    out_path = os.path.join(os.path.dirname(__file__), "FLAGSHIP_PROSPECT_DOSSIERS.md")
    export_dossiers_to_file(out_path)
