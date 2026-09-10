"""
SMB Healthcare AI - Carrier Gateway & Live Cellular SMS Webhook Relay.

Provides production-ready carrier integration for Telnyx and Twilio, supporting
physical phone two-way texting, TCPA 10DLC compliance, STOP opt-out automation,
and sub-10ms atomic slot claiming across Dental and Med Spa practices.
"""

from .sms_relay import CarrierSMSGateway

__all__ = ["CarrierSMSGateway"]
