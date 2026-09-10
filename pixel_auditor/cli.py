"""
Command-Line Interface for Empirical Pixel Auditor.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from pixel_auditor.auditor import PixelAuditor
from pixel_auditor.scorecard_generator import ScorecardGenerator


async def run_cli(target_url: str, output_path: str):
    print("=" * 80)
    print(f"  COMMENCING FORENSIC TRACKING PIXEL AUDIT: {target_url}")
    print("=" * 80)
    print("[*] Inspecting booking funnel DOM, network beacons, and GTM containers...")

    auditor = PixelAuditor(target_url)
    results = await auditor.scan_live_url()

    if results.get("error"):
        print(f"[-] Scan error: {results['error']}")
        sys.exit(1)

    print(f"\n[+] Scan Complete!")
    print(f"    - Hard Gate U-HG-02: {results['hard_gate_verdict']}")
    print(f"    - Risk Rating:       {results['risk_rating']}")
    print(f"    - Trackers Found:    {results['total_violations']}")

    if results['violations']:
        print("\n[-] VIOLATIONS DETECTED:")
        for idx, v in enumerate(results['violations'], 1):
            print(f"    [{idx}] {v['tracker']} ({v['severity']}) -> {v['host']}")
            if v.get('detected_clinical_terms'):
                print(f"        EXFILTRATED PHI: {v['detected_clinical_terms']}")

    # Generate Scorecard HTML
    html = ScorecardGenerator.generate_html(results)
    out_file = Path(output_path)
    out_file.write_text(html, encoding="utf-8")
    print(f"\n[*] Executive 1-Page Scorecard HTML saved to: {out_file.resolve()}")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Empirical Tracking Pixel & Telemetry Auditor")
    parser.add_argument("url", help="Target clinic booking funnel URL")
    parser.add_argument("--output", default="prospect_audit_scorecard.html", help="Output HTML scorecard path")
    args = parser.parse_args()

    asyncio.run(run_cli(args.url, args.output))


if __name__ == "__main__":
    main()
