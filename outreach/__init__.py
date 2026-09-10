"""
Outreach and Business Development Suite for Lane 3 Healthcare AI.

Provides personalized multi-channel outreach campaigns, prospect dossiers,
executive one-page leave-behinds, and objection handling for dental and aesthetic practices.
"""

from .campaign_templates import (
    OutreachTouch,
    OutreachSequence,
    CampaignTemplateEngine,
    ProspectProfile,
    generate_prospect_campaign
)

__all__ = [
    "OutreachTouch",
    "OutreachSequence",
    "CampaignTemplateEngine",
    "ProspectProfile",
    "generate_prospect_campaign"
]
