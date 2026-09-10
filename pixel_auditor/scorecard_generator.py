"""
Executive Compliance & Privacy Audit Scorecard Generator.

Transforms empirical telemetry audit results into a high-impact, 1-page executive
scorecard (HTML / Markdown) for prospect presentations.
"""

from typing import Dict, Any

class ScorecardGenerator:
    """
    Generates presentation-ready client audit scorecards.
    """
    @staticmethod
    def generate_html(audit_data: Dict[str, Any]) -> str:
        verdict = audit_data.get("hard_gate_verdict", "UNKNOWN")
        risk = audit_data.get("risk_rating", "HIGH")
        target_url = audit_data.get("target_url", "")
        violations = audit_data.get("violations", [])
        total_violations = audit_data.get("total_violations", len(violations))
        exposure = audit_data.get("statutory_daily_exposure", 50120)

        badge_color = "#10B981" if risk == "LOW" else ("#EF4444" if risk == "CRITICAL" else "#F59E0B")
        badge_bg = "#ECFDF5" if risk == "LOW" else ("#FEF2F2" if risk == "CRITICAL" else "#FFFBEB")

        # Table rows
        table_rows = ""
        if violations:
            for idx, v in enumerate(violations, 1):
                sev_color = "#DC2626" if v["severity"] == "CRITICAL" else "#D97706"
                clinical_badge = ""
                if v.get("detected_clinical_terms"):
                    terms_str = ", ".join(v["detected_clinical_terms"])
                    clinical_badge = f"<span class='tag-clinical'>PHI Exfiltration: {terms_str}</span>"

                table_rows += f"""
                <tr>
                    <td style="font-weight: 600; color: #0F172A;">{idx}. {v['tracker']}</td>
                    <td><code>{v['host']}</code></td>
                    <td><span style="color: {sev_color}; font-weight: 700;">{v['severity']}</span></td>
                    <td><div style="font-size: 12px; color: #475569; word-break: break-all;">{v['url']}</div>{clinical_badge}</td>
                </tr>
                """
        else:
            table_rows = """
            <tr>
                <td colspan="4" style="text-align: center; padding: 24px; color: #059669; font-weight: 600;">
                    ✓ Zero third-party advertising trackers detected on booking funnel. 100% U-HG-02 Compliant!
                </td>
            </tr>
            """

        alert_box = ""
        if total_violations > 0:
            alert_box = """<div class="statutory-alert">
                <h3>Statutory & Regulatory Breach Alert (FTC HBNR & WA MHMDA)</h3>
                <p>Third-party advertising scripts detected on interactive scheduling paths transmit patient visit intent, IP addresses, and procedure interest to commercial data brokers without HIPAA Business Associate Agreements. Under FTC 16 CFR 318, failure to notify affected individuals incurs civil penalties up to <strong>$50,120 per violation per day</strong>.</p>
            </div>"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HIPAA & FTC Digital Telemetry Audit Scorecard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
        body {{ background-color: #F8FAFC; color: #1E293B; padding: 32px 16px; }}
        .container {{ max-width: 900px; margin: 0 auto; background: #FFFFFF; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); border: 1px solid #E2E8F0; overflow: hidden; }}
        .header {{ background: #0F172A; color: #FFFFFF; padding: 28px 32px; display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #0EA5E9; }}
        .header h1 {{ font-size: 20px; font-weight: 700; letter-spacing: -0.02em; }}
        .header .subtitle {{ font-size: 13px; color: #94A3B8; margin-top: 4px; }}
        .badge {{ padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; background: {badge_bg}; color: {badge_color}; border: 1px solid {badge_color}; }}
        
        .content {{ padding: 32px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 28px; }}
        .metric-card {{ background: #F1F5F9; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px 20px; }}
        .metric-label {{ font-size: 11px; text-transform: uppercase; color: #64748B; font-weight: 600; letter-spacing: 0.04em; }}
        .metric-val {{ font-size: 22px; font-weight: 800; color: #0F172A; margin-top: 6px; }}
        .metric-sub {{ font-size: 11px; color: #64748B; margin-top: 2px; }}

        .statutory-alert {{ background: #FEF2F2; border-left: 4px solid #EF4444; padding: 18px 20px; border-radius: 0 8px 8px 0; margin-bottom: 28px; }}
        .statutory-alert h3 {{ font-size: 14px; color: #991B1B; font-weight: 700; }}
        .statutory-alert p {{ font-size: 13px; color: #7F1D1D; margin-top: 4px; line-height: 1.5; }}

        .section-title {{ font-size: 15px; font-weight: 700; color: #0F172A; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 0.03em; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 28px; font-size: 13px; }}
        th {{ background: #F8FAFC; text-align: left; padding: 12px 14px; color: #475569; font-weight: 600; border-bottom: 1px solid #CBD5E1; }}
        td {{ padding: 12px 14px; border-bottom: 1px solid #E2E8F0; vertical-align: top; }}
        code {{ background: #E2E8F0; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 12px; color: #0F172A; }}
        .tag-clinical {{ display: inline-block; background: #FEE2E2; color: #B91C1C; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; margin-top: 4px; }}

        .remediation-box {{ background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 20px; }}
        .remediation-box h4 {{ font-size: 14px; color: #0F172A; font-weight: 700; margin-bottom: 10px; }}
        .remediation-box ol {{ padding-left: 20px; font-size: 13px; color: #334155; line-height: 1.6; }}

        .footer {{ background: #F8FAFC; border-top: 1px solid #E2E8F0; padding: 16px 32px; font-size: 11px; color: #64748B; display: flex; justify-content: space-between; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>Forensic Telemetry & Tracking Pixel Audit</h1>
                <div class="subtitle">Target: <strong>{target_url}</strong></div>
            </div>
            <div class="badge">{risk} RISK RATING</div>
        </div>

        <div class="content">
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Universal Hard Gate U-HG-02</div>
                    <div class="metric-val" style="color: {badge_color};">{verdict.split()[0]}</div>
                    <div class="metric-sub">{verdict}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Detected Ad Trackers</div>
                    <div class="metric-val">{total_violations}</div>
                    <div class="metric-sub">Marketing Beacons on Funnel</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Max Statutory Daily Exposure</div>
                    <div class="metric-val" style="color: #DC2626;">${exposure:,}</div>
                    <div class="metric-sub">FTC HBNR Penalties / Day</div>
                </div>
            </div>

            {alert_box}

            <div class="section-title">Forensic Detection Matrix</div>
            <table>
                <thead>
                    <tr>
                        <th style="width: 25%;">Tracker / Network</th>
                        <th style="width: 25%;">Destination Host</th>
                        <th style="width: 15%;">Severity</th>
                        <th style="width: 35%;">Exfiltration Details</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>

            <div class="remediation-box">
                <h4>Recommended 3-Step Forensic Remediation</h4>
                <ol>
                    <li><strong>Google Tag Manager Sanitization:</strong> Implement a Page Path Blocking Exception trigger matching <code>.*(book|schedule|appointment|intake).*</code> across all Meta, TikTok, and Google Ads conversion tags.</li>
                    <li><strong>EHR / Booking Platform Isolation:</strong> Blank the Meta Pixel ID and Google Analytics Measurement ID inside the booking vendor dashboard (Boulevard / Zenoti / Tebra).</li>
                    <li><strong>Deploy Zero-Pixel Middleware:</strong> Migrate patient scheduling and waitlist recovery to Lane 3 open agent architecture, operating with 0.0% third-party client telemetry.</li>
                </ol>
            </div>
        </div>

        <div class="footer">
            <div>Generated by Lane 3 SMB Healthcare AI Suite &bull; Governing Standard: DOC-AA-01 / U-HG-02</div>
            <div>Strictly Confidential &bull; For Practice Leadership & Legal Counsel Only</div>
        </div>
    </div>
</body>
</html>
"""
        return html

    @staticmethod
    def generate_markdown(audit_data: Dict[str, Any]) -> str:
        verdict = audit_data.get("hard_gate_verdict", "UNKNOWN")
        risk = audit_data.get("risk_rating", "HIGH")
        target_url = audit_data.get("target_url", "")
        violations = audit_data.get("violations", [])

        md = f"""# Forensic Telemetry Audit Report: {target_url}

- **Audit Date**: {audit_data.get('timestamp', 'N/A')}
- **Universal Hard Gate U-HG-02 Verdict**: **{verdict}**
- **Risk Rating**: **{risk}**
- **Total Ad Trackers Detected**: {len(violations)}
- **Max Statutory Exposure**: ${audit_data.get('statutory_daily_exposure', 50120):,} / day

## Detected Trackers & Telemetry Leaks

| Tracker | Destination Host | Severity | Exfiltrated Terms |
|---|---|---|---|
"""
        for v in violations:
            terms = ", ".join(v.get("detected_clinical_terms", [])) or "None"
            md += f"| {v['tracker']} | `{v['host']}` | **{v['severity']}** | {terms} |\\n"

        md += """
## Recommended Action Plan
1. Add GTM blocking triggers on `/book*` and `/schedule*` paths.
2. Blank pixel ID inputs in booking software admin settings.
3. Deploy Lane 3 Zero-Pixel middleware.
"""
        return md
