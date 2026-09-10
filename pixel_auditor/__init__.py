"""
SMB Healthcare AI - Empirical Tracking Pixel & Telemetry Auditor Package.

Audits dental and aesthetic med spa booking funnels in real time, detecting
unauthorized Meta, Google, TikTok, and session replay trackers under HHS OCR,
FTC Health Breach Notification Rule (HBNR), and Universal Hard Gate U-HG-02.
"""

from .auditor import PixelAuditor
from .scorecard_generator import ScorecardGenerator

__all__ = ["PixelAuditor", "ScorecardGenerator"]
