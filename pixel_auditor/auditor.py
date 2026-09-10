"""
High-Speed Empirical Tracking Pixel & Telemetry Auditor.

Inspects target website DOMs, network resources, and booking funnels to detect
third-party advertising pixels and Protected Health Information (PHI) exfiltration.
"""

import asyncio
import re
import time
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx

# Forbidden advertising and tracking networks
FORBIDDEN_TRACKER_HOSTS = {
    "connect.facebook.net": "Meta (Facebook) Pixel",
    "facebook.com/tr": "Meta (Facebook) Pixel Event Beacon",
    "google-analytics.com": "Google Analytics (GA4)",
    "googletagmanager.com": "Google Tag Manager Container",
    "analytics.tiktok.com": "TikTok Pixel",
    "criteo.net": "Criteo Advertising Tracker",
    "bat.bing.com": "Microsoft Bing Ads Universal Event Tracking (UET)",
    "ct.pinterest.com": "Pinterest Conversions Tag",
    "snap.licdn.com": "LinkedIn Insight Tag",
    "hotjar.com": "Hotjar Session Replay (Keystroke Risk)",
    "fullstory.com": "FullStory Session Replay (Keystroke Risk)",
    "clarity.ms": "Microsoft Clarity Session Recorder"
}

# Protected procedural and clinical descriptors
SENSITIVE_CLINICAL_TERMS = [
    "botox", "dysport", "xeomin", "filler", "juvederm", "restylane", "voluma",
    "morpheus8", "microneedling", "coolsculpting", "semaglutide", "tirzepatide",
    "ozempic", "weight loss", "hormone", "hrt", "testosterone", "bbl",
    "liposuction", "facelift", "implant", "root canal", "extraction", "crown",
    "periodontal", "invisalign", "teeth whitening", "veneer", "sedation"
]

# Booking widget iframes
KNOWN_BOOKING_IFRAMES = {
    "joinblvd.com": "Boulevard Online Booking",
    "zenoti.com": "Zenoti Online Webstore",
    "embed.nexhealth.com": "NexHealth Online Scheduling",
    "patientpop.com": "Tebra / PatientPop Booking",
    "weave.com": "Weave Online Scheduling",
    "doctor.com": "Doctor.com / Press Ganey Scheduling"
}


class PixelAuditor:
    """
    Empirical Tracking Pixel & Telemetry Auditor.
    """
    def __init__(self, target_url: str, timeout: float = 15.0):
        self.target_url = target_url
        self.timeout = timeout
        self.violations: List[Dict[str, Any]] = []
        self.detected_iframes: List[Dict[str, str]] = []
        self.total_scripts_scanned = 0

    async def audit_html_content(self, html: str, base_url: str) -> Dict[str, Any]:
        """Audits raw HTML string for embedded tracking scripts and iframes."""
        self.violations = []
        self.detected_iframes = []
        
        # 1. Extract script tags
        script_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
        inline_scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
        self.total_scripts_scanned = len(script_srcs) + len(inline_scripts)

        # 2. Extract iframes
        iframe_srcs = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
        for src in iframe_srcs:
            for iframe_host, vendor in KNOWN_BOOKING_IFRAMES.items():
                if iframe_host in src:
                    self.detected_iframes.append({"vendor": vendor, "url": src})

        # 3. Inspect script sources against tracker registry
        for src in script_srcs:
            for host_pattern, tracker_name in FORBIDDEN_TRACKER_HOSTS.items():
                if host_pattern in src.lower():
                    # Check for clinical terms in script URL
                    detected_terms = [
                        term for term in SENSITIVE_CLINICAL_TERMS
                        if term in src.lower()
                    ]
                    self.violations.append({
                        "tracker": tracker_name,
                        "host": host_pattern,
                        "type": "External Script Beacon",
                        "url": src[:200] + ("..." if len(src) > 200 else ""),
                        "detected_clinical_terms": detected_terms,
                        "severity": "CRITICAL" if detected_terms or "facebook" in host_pattern or "tiktok" in host_pattern else "HIGH"
                    })

        # 4. Inspect inline scripts for tracker initialization IDs
        full_inline_text = " ".join(inline_scripts)
        if "fbq(" in full_inline_text or "connect.facebook.net" in full_inline_text:
            meta_pixel_ids = re.findall(r"fbq\(['\"]init['\"],\s*['\"](\d+)['\"]", full_inline_text)
            self.violations.append({
                "tracker": "Meta (Facebook) Pixel Inline Initialization",
                "host": "connect.facebook.net",
                "type": "Client-Side DOM Initialization",
                "url": f"Pixel ID(s): {', '.join(meta_pixel_ids) if meta_pixel_ids else 'Embedded fbq script'}",
                "detected_clinical_terms": [],
                "severity": "CRITICAL"
            })

        if "gtag(" in full_inline_text or "googletagmanager.com" in full_inline_text:
            ga4_ids = re.findall(r"['\"](G-[A-Z0-9]+)['\"]", full_inline_text)
            if ga4_ids:
                self.violations.append({
                    "tracker": "Google Analytics 4 (GA4) Tag",
                    "host": "google-analytics.com",
                    "type": "Measurement ID Injection",
                    "url": f"Measurement ID(s): {', '.join(set(ga4_ids))}",
                    "detected_clinical_terms": [],
                    "severity": "HIGH"
                })

        # 5. Inspect target URL parameters for leaked clinical terms
        parsed_target = urllib.parse.urlparse(base_url)
        url_clinical_terms = [
            term for term in SENSITIVE_CLINICAL_TERMS
            if term in parsed_target.query.lower() or term in parsed_target.path.lower()
        ]

        if url_clinical_terms and len(self.violations) > 0:
            for v in self.violations:
                v["detected_clinical_terms"] = list(set(v["detected_clinical_terms"] + url_clinical_terms))
                v["severity"] = "CRITICAL"

        # Hard Gate Evaluation
        is_pass = len(self.violations) == 0
        critical_count = sum(1 for v in self.violations if v["severity"] == "CRITICAL")

        verdict = {
            "target_url": base_url,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "hard_gate_verdict": "PASS (U-HG-02 Compliant)" if is_pass else "FAIL (U-HG-02 Violation)",
            "risk_rating": "LOW" if is_pass else ("CRITICAL" if critical_count > 0 else "HIGH"),
            "total_scripts_scanned": self.total_scripts_scanned,
            "total_violations": len(self.violations),
            "critical_violations": critical_count,
            "detected_iframes": self.detected_iframes,
            "violations": self.violations,
            "statutory_daily_exposure": 0 if is_pass else 50120
        }
        return verdict

    async def scan_live_url(self) -> Dict[str, Any]:
        """Performs live HTTP scan against target URL."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=self.timeout) as client:
                resp = await client.get(self.target_url, headers=headers)
                return await self.audit_html_content(resp.text, str(resp.url))
        except Exception as e:
            return {
                "target_url": self.target_url,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "hard_gate_verdict": "ERROR",
                "risk_rating": "UNKNOWN",
                "error": str(e),
                "total_violations": 0,
                "violations": []
            }
