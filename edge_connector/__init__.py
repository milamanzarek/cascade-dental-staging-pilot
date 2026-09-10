"""
SMB Healthcare AI - Lane 3 Zero-Port Clinic Edge Connector Package.

Provides an outbound-only, TLS 1.3 / WebSocket reverse-tunnel connecting on-premise
dental and med spa databases (Open Dental, Dentrix, Eaglesoft) to cloud agents
without requiring open inbound router ports or VPN infrastructure.
"""

from .cloud_gateway import CloudGateway
from .clinic_daemon import ClinicDaemon, PHISanitizer

__all__ = ["CloudGateway", "ClinicDaemon", "PHISanitizer"]
