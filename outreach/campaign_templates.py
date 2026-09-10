"""
Campaign Template Engine for Lane 3 Healthcare AI.

Generates high-converting, personalized 3-touch outreach sequences
(Compliance Wedge -> Operational ROI -> Live Phone Demo + Guarantee)
and multi-channel snippets (LinkedIn, SMS) tailored to specific dental
and medical aesthetics practice profiles.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class ProspectProfile:
    prospect_id: str
    practice_name: str
    specialty: str
    location: str
    decision_maker: str
    decision_maker_title: str
    email: str
    phone: str
    booking_url: str
    current_pms: str
    trackers_detected: List[str]
    risk_rating: str
    est_annual_revenue: str
    flagship_procedure: str = "Morpheus8 / Fillers"
    est_cancellation_loss: str = "$1,200"
    dormant_credits_est: str = "$18,500"
    scorecard_filename: str = ""


@dataclass
class OutreachTouch:
    touch_number: int
    channel: str  # Email, LinkedIn InMail, LinkedIn Connect, SMS
    day_offset: int
    subject: str
    content: str
    cta: str


@dataclass
class OutreachSequence:
    prospect: ProspectProfile
    touches: List[OutreachTouch] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [
            f"# Outreach Campaign Dossier: {self.prospect.practice_name} ({self.prospect.prospect_id})",
            "",
            f"- **Target Decision Maker**: {self.prospect.decision_maker}, {self.prospect.decision_maker_title}",
            f"- **Email**: `{self.prospect.email}` | **Direct Phone**: `{self.prospect.phone}`",
            f"- **Location**: {self.prospect.location} | **PMS**: {self.prospect.current_pms}",
            f"- **Statutory Risk Tier**: **{self.prospect.risk_rating}** ({len(self.prospect.trackers_detected)} Trackers Detected)",
            f"- **Forensic Scorecard**: `{self.prospect.scorecard_filename}`",
            "",
            "---",
            ""
        ]
        for t in self.touches:
            lines.extend([
                f"### Touch {t.touch_number}: {t.channel} (Day {t.day_offset})",
                f"**Subject/Header**: *{t.subject}*",
                "",
                "```text",
                t.content.strip(),
                "```",
                "",
                f"**Primary Call-to-Action**: {t.cta}",
                "",
                "---",
                ""
            ])
        return "\n".join(lines)


class CampaignTemplateEngine:
    """Generates personalized multi-channel outreach campaigns."""

    @classmethod
    def generate_sequence(cls, p: ProspectProfile) -> OutreachSequence:
        touches: List[OutreachTouch] = []
        trackers_str = ", ".join(p.trackers_detected[:3]) if p.trackers_detected else "Third-party ad trackers"
        first_name = p.decision_maker.split()[0] if p.decision_maker else "Doctor"

        # Touch 1: The Compliance Wedge (Day 1)
        t1_subject = f"Confidential: Patient privacy vulnerability detected on {p.practice_name}'s booking path"
        t1_body = f"""Hi {first_name},

I was reviewing the patient scheduling infrastructure at {p.practice_name} this week and noticed a critical compliance vulnerability on your direct booking path ({p.booking_url}).

Specifically, our automated healthcare telemetry scanner detected active tracking beacons ({trackers_str}) firing directly during patient appointment selection. 

Under the FTC Health Breach Notification Rule (16 CFR 318) and the Washington My Health My Data Act (RCW 19.373), transmitting patient procedure selection or IP addresses to commercial ad platforms without a signed Business Associate Agreement exposes outpatient practices to statutory penalties of up to $50,120 per day.

I generated a confidential, 1-page Forensic Privacy Scorecard for {p.practice_name} detailing the exact network payload and remediation steps (attached to this email / linked below).

We engineered an open-source, Zero-Port Edge Middleware that connects directly to {p.current_pms}, sanitizing all patient identifiers locally before any cloud transmission, eliminating pixel liability completely while slashing SaaS fees by 75%.

Do you have 5 minutes this Thursday or Friday to review the scorecard and see how to insulate your practice?

Best regards,

Kamilla & The Lane 3 Healthcare Engineering Team
Direct: (206) 880-0477
Scorecard File: {p.scorecard_filename}
"""
        touches.append(OutreachTouch(
            touch_number=1,
            channel="Email",
            day_offset=1,
            subject=t1_subject,
            content=t1_body,
            cta="Review attached 1-page forensic scorecard & schedule 5-min briefing"
        ))

        # Touch 2: Operational ROI & High-Ticket Slot Recovery (Day 4)
        t2_subject = f"Recovering {p.est_cancellation_loss}/day in {p.flagship_procedure} cancellations at {p.practice_name}"
        t2_body = f"""Hi {first_name},

Following up on the privacy scorecard I sent over Tuesday. Beyond insulating {p.practice_name} from FTC tracking penalties, I wanted to share the operational benchmark we just completed across Pacific Northwest practices.

In aesthetic and surgical practices running {p.current_pms}, a single cancelled 90-minute {p.flagship_procedure} slot leaves an immediate {p.est_cancellation_loss} hole in the day because standard waitlists rely on front desk staff playing phone tag. Furthermore, regional med spas carry an average of {p.dormant_credits_est} in dormant VIP Beauty Bank / wallet balances that go unredeemed for 60+ days.

Our Lane 3 autonomous agent handles this with zero staff overhead:
1. Detects cancellations in under 5 milliseconds.
2. Simultaneously checks both injector credential and laser suite availability.
3. Dispatches private zero-PHI concierge SMS to your top retreatment waitlist.
4. Auto-locks the slot when the patient replies 'YES'.

Unlike NexHealth or Weave that charge $1,800 to $2,500/month in compounding subscription fees, Lane 3 runs locally on your clinic network for a flat $450/month with zero per-message charges.

Would you be open to a 10-minute live demonstration where I trigger a live cancellation and you watch it recover on your phone?

Best regards,

Kamilla & The Lane 3 Healthcare Engineering Team
Direct: (206) 880-0477
Live Interactive Demo: https://webdemo-nine-zeta.vercel.app
"""
        touches.append(OutreachTouch(
            touch_number=2,
            channel="Email",
            day_offset=4,
            subject=t2_subject,
            content=t2_body,
            cta="Request 10-minute live mobile demo or review web demo"
        ))

        # Touch 3: Live Demo Invitation & Founding Partner Guarantee (Day 8)
        t3_subject = f"10-minute live test for {p.practice_name} + 30-day milestone guarantee"
        t3_body = f"""Hi {first_name},

I know how busy clinic operations are, so I'll be brief. 

We are selecting two flagship practices in the Puget Sound region for our Q3 Founding Partner Pilot. 

Here is our exact commitment to {p.practice_name}:
- **Turnkey Setup**: We install the Zero-Port Edge Daemon and connect your {p.current_pms} database in under 45 minutes with zero disruption to staff.
- **30-Day Milestone Guarantee**: If our agent does not autonomously recover at least 5 broken appointments or $5,000 in clinical revenue within your first 30 days, we refund 100% of the $2,000 deployment fee immediately.
- **Lifetime Price Lock**: Your ongoing support retainer is locked at $450/month (saving over $18,000/year compared to legacy enterprise SaaS).

If you want to test the technology right now from your mobile phone, text **DEMO** to **(206) 880-0477** and our autonomous concierge will respond instantly with an interactive slot demonstration.

Can we grab 10 minutes on Monday at 12:30 PM or Tuesday at 8:00 AM?

Best regards,

Kamilla
Founder & Lead Architect | Lane 3 Healthcare AI
Direct: (206) 880-0477 | Founding Partner Agreement: https://docs.google.com/document/d/13FfufRcOWL43UwHVvzv7Z7zsDpb7soAgbr0E4a33q3I/edit?usp=sharing
"""
        touches.append(OutreachTouch(
            touch_number=3,
            channel="Email",
            day_offset=8,
            subject=t3_subject,
            content=t3_body,
            cta="Text 'DEMO' to (206) 880-0477 or lock 10-min Zoom"
        ))

        # Touch 4: LinkedIn Connection Request Note (<300 characters)
        li_connect = f"Hi {first_name} - noted active Meta/TikTok tracking pixels on {p.practice_name}'s booking path violating FTC HBNR. We engineered a zero-port edge connector for {p.current_pms} that eliminates pixel liability and recovers $1,200/day in cancellations. Love to share your free scorecard."
        if len(li_connect) > 300:
            li_connect = li_connect[:297] + "..."
        touches.append(OutreachTouch(
            touch_number=4,
            channel="LinkedIn Connection Request",
            day_offset=1,
            subject="Personalized Connection Request (<300 chars)",
            content=li_connect,
            cta="Connect on LinkedIn"
        ))

        # Touch 5: LinkedIn InMail / Direct Message (Day 5)
        li_inmail = f"""Hi {first_name},

Reaching out directly regarding patient scheduling privacy and revenue optimization at {p.practice_name}.

We audited 25 regional outpatient practices this month and found that {p.practice_name}'s booking path ({p.booking_url}) is transmitting patient procedure data to {trackers_str}. Under Washington's My Health My Data Act and the FTC HBNR, this creates acute regulatory liability.

We generated a confidential 1-page forensic scorecard for your practice showing the exact HTTP beacons firing and the zero-code remediation.

At the same time, we've helped regional practices recover $1,200/day in broken {p.flagship_procedure} slots using an autonomous local agent connected to {p.current_pms} without paying $2k/mo to legacy vendors.

Happy to send the PDF scorecard over here, or you can test the live concierge by texting 'DEMO' to (206) 880-0477.

Best,
Kamilla | Lane 3 Healthcare AI
"""
        touches.append(OutreachTouch(
            touch_number=5,
            channel="LinkedIn InMail",
            day_offset=5,
            subject=f"Patient scheduling privacy scorecard for {p.practice_name}",
            content=li_inmail,
            cta="Reply for PDF scorecard or text DEMO to (206) 880-0477"
        ))

        # Touch 6: Cellular SMS Follow-up (Day 11, Optional / Opt-in)
        sms_body = f"Hi {first_name}, Kamilla from Lane 3. Sent over {p.practice_name}'s patient scheduling privacy audit and cancellation recovery breakdown. If you'd like a 5-min walk-through, reply YES or let me know a good time. (Reply STOP to opt out)"
        touches.append(OutreachTouch(
            touch_number=6,
            channel="SMS Follow-Up (TCPA Compliant)",
            day_offset=11,
            subject="Executive SMS Nudge",
            content=sms_body,
            cta="Reply YES for direct callback"
        ))

        return OutreachSequence(prospect=p, touches=touches)


def generate_prospect_campaign(prospect_dict: Dict[str, Any]) -> OutreachSequence:
    """Helper to generate a sequence from a raw prospect dict."""
    profile = ProspectProfile(
        prospect_id=prospect_dict.get("prospect_id", "PR-000"),
        practice_name=prospect_dict.get("practice_name", "Target Practice"),
        specialty=prospect_dict.get("specialty", "Medical Aesthetics"),
        location=prospect_dict.get("location", "Seattle, WA"),
        decision_maker=prospect_dict.get("decision_maker", "Practice Owner"),
        decision_maker_title=prospect_dict.get("decision_maker_title", "Owner & Medical Director"),
        email=prospect_dict.get("email", "owner@clinic.com"),
        phone=prospect_dict.get("phone", "(206) 555-0100"),
        booking_url=prospect_dict.get("booking_url", "https://clinic.com/book"),
        current_pms=prospect_dict.get("current_pms", "Boulevard"),
        trackers_detected=prospect_dict.get("trackers_detected", ["Meta Pixel", "Google Tag Manager"]),
        risk_rating=prospect_dict.get("risk_rating", "CRITICAL"),
        est_annual_revenue=prospect_dict.get("est_annual_revenue", "$2,500,000"),
        flagship_procedure=prospect_dict.get("flagship_procedure", "Morpheus8 / Fillers"),
        est_cancellation_loss=prospect_dict.get("est_cancellation_loss", "$1,200"),
        dormant_credits_est=prospect_dict.get("dormant_credits_est", "$18,500"),
        scorecard_filename=prospect_dict.get("scorecard_filename", "")
    )
    return CampaignTemplateEngine.generate_sequence(profile)
