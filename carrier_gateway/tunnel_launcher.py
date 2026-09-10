"""
Carrier Webhook Tunnel Launcher & Diagnostic Guide.

Helps the user launch local tunnels (e.g. ngrok or Cloudflare Tunnel) to connect
a live physical mobile phone (AT&T, Verizon, T-Mobile) to the Carrier Gateway during
client prospect demonstrations.
"""

import sys
import shutil

def print_guide(port: int = 8768):
    print("=" * 80)
    print("  LANE 3 LIVE MOBILE SMS CONNECTIVITY: PROSPECT PRESENTATION GUIDE")
    print("=" * 80)
    print(f"\n[*] Carrier Gateway Local Listening Port: {port}\n")
    print("Step 1: Launch Local Tunnel (Choose Option A or Option B)")
    print("  Option A (ngrok):")
    print(f"      ngrok http {port}")
    print("      -> Forwarding URL: https://<your-subdomain>.ngrok-free.app\n")
    print("  Option B (Cloudflare Tunnel):")
    print(f"      cloudflared tunnel --url http://localhost:{port}\n")
    
    print("Step 2: Configure Webhook in Carrier Console:")
    print("  - Twilio Console -> Phone Numbers -> Active Numbers -> Webhook Configuration:")
    print(f"      URL: https://<your-subdomain>.ngrok-free.app/webhooks/twilio/inbound")
    print("      HTTP Method: HTTP POST\n")
    print("  - Telnyx Portal -> Messaging -> Messaging Profiles -> Inbound Settings:")
    print(f"      Webhook URL: https://<your-subdomain>.ngrok-free.app/webhooks/telnyx/inbound")
    print("      Webhook API Version: API v2 (POST)\n")

    print("Step 3: Live Inbound Testing from Physical Phone:")
    print("  1. Send text 'YES' from your phone to the carrier number.")
    print("  2. Watch the terminal atomically book the patient and return confirmation SMS.")
    print("  3. Text 'STOP' to verify instant TCPA unsubscription.")
    print("=" * 80)

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8768
    print_guide(port)
