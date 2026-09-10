"""
Interactive and Scriptable Clinic Edge Configuration Wizard.

Validates PMS connection parameters, tests outbound TLS 443 gateway handshakes,
and outputs secure local environment files (.env.clinic).
"""

import os
import sys
import json
import socket
import ssl
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any


class PMSType(str, Enum):
    OPEN_DENTAL = "open_dental"
    BOULEVARD = "boulevard"
    ZENOTI = "zenoti"
    SQLITE_MOCK = "sqlite_mock"


class CarrierType(str, Enum):
    TELNYX = "telnyx"
    TWILIO = "twilio"


@dataclass
class ClinicConfig:
    clinic_id: str
    clinic_name: str
    pms_type: PMSType
    db_path: str
    gateway_url: str
    api_token: str
    carrier_type: CarrierType = CarrierType.TELNYX
    emergency_forwarding_phone: str = "+12065550199"
    log_level: str = "INFO"
    enable_zero_port_tunnel: bool = True
    phi_sanitization_strict: bool = True

    def validate(self) -> Tuple[bool, List[str]]:
        errors = []
        if not self.clinic_id or len(self.clinic_id) < 3:
            errors.append("clinic_id must be at least 3 characters")
        if not self.clinic_name:
            errors.append("clinic_name cannot be empty")
        if not self.gateway_url.startswith(("wss://", "https://")):
            errors.append("gateway_url must use TLS (wss:// or https://)")
        if not self.api_token or len(self.api_token) < 8:
            errors.append("api_token must be at least 8 characters")
        return (len(errors) == 0, errors)

    def to_env_content(self) -> str:
        lines = [
            "# Lane 3 Clinic Edge Configuration - Auto-generated",
            f"LANE3_CLINIC_ID={self.clinic_id}",
            f"LANE3_CLINIC_NAME={self.clinic_name}",
            f"LANE3_PMS_TYPE={self.pms_type.value}",
            f"LANE3_DB_PATH={self.db_path}",
            f"LANE3_GATEWAY_URL={self.gateway_url}",
            f"LANE3_API_TOKEN={self.api_token}",
            f"LANE3_CARRIER_PROVIDER={self.carrier_type.value}",
            f"LANE3_EMERGENCY_PHONE={self.emergency_forwarding_phone}",
            f"LANE3_LOG_LEVEL={self.log_level}",
            f"LANE3_ZERO_PORT_TUNNEL={str(self.enable_zero_port_tunnel).lower()}",
            f"LANE3_PHI_SANITIZER={str(self.phi_sanitization_strict).lower()}"
        ]
        return "\n".join(lines) + "\n"


def run_preflight_checks(gateway_host: str, gateway_port: int = 443, timeout: float = 3.0) -> Tuple[bool, str]:
    """
    Verifies that the clinic server can establish an outbound TLS connection
    to the cloud gateway without opening any inbound firewall ports.
    """
    try:
        context = ssl.create_default_context()
        with socket.create_connection((gateway_host, gateway_port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=gateway_host) as ssock:
                version = ssock.version()
                return True, f"Outbound TLS connection successful ({version}) on port {gateway_port}"
    except Exception as e:
        return False, f"Preflight connection failed: {str(e)}"


class ConfigWizardEngine:
    """Manages configuration creation, file export, and verification."""

    @classmethod
    def generate_and_save(cls, config: ClinicConfig, output_dir: str) -> str:
        is_valid, errors = config.validate()
        if not is_valid:
            raise ValueError(f"Invalid Clinic Configuration: {', '.join(errors)}")

        os.makedirs(output_dir, exist_ok=True)
        env_path = os.path.join(output_dir, ".env.clinic")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(config.to_env_content())
            
        json_path = os.path.join(output_dir, "clinic_config.json")
        data = asdict(config)
        # Redact token for logging/json safety
        data["api_token"] = data["api_token"][:4] + "..." + data["api_token"][-4:] if len(data["api_token"]) > 8 else "***"
        data["pms_type"] = config.pms_type.value
        data["carrier_type"] = config.carrier_type.value
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return env_path


def interactive_cli():
    print("=" * 65)
    print("  LANE 3 HEALTHCARE AI: WINDOWS CLINIC EDGE SETUP WIZARD")
    print("=" * 65)
    print("This wizard configures the local edge daemon on your clinic server.\n")

    clinic_id = input("Enter Clinic ID [PR-001]: ").strip() or "PR-001"
    clinic_name = input("Enter Clinic Name [Bellevue Aesthetic Medicine]: ").strip() or "Bellevue Aesthetic Medicine"
    
    print("\nSelect Practice Management System:")
    print("  1) Open Dental (MySQL / MariaDB)")
    print("  2) Boulevard (Cloud GraphQL)")
    print("  3) Zenoti (Cloud REST)")
    print("  4) SQLite Mock (Testing / Sandbox)")
    choice = input("Enter choice [1-4, default 4]: ").strip() or "4"
    pms_map = {"1": PMSType.OPEN_DENTAL, "2": PMSType.BOULEVARD, "3": PMSType.ZENOTI, "4": PMSType.SQLITE_MOCK}
    pms = pms_map.get(choice, PMSType.SQLITE_MOCK)

    db_path = input("Enter Database Path or Connection String [data/clinic.db]: ").strip() or "data/clinic.db"
    gateway = input("Enter Gateway URL [wss://gateway.lane3healthcare.com/ws/edge]: ").strip() or "wss://gateway.lane3healthcare.com/ws/edge"
    token = input("Enter Clinic Auth Token [test_token_secret_12345]: ").strip() or "test_token_secret_12345"

    config = ClinicConfig(
        clinic_id=clinic_id,
        clinic_name=clinic_name,
        pms_type=pms,
        db_path=db_path,
        gateway_url=gateway,
        api_token=token
    )

    out_dir = r"C:\Lane3Edge\config" if os.name == "nt" else "./config"
    path = ConfigWizardEngine.generate_and_save(config, out_dir)
    print(f"\nConfiguration saved successfully to {path}!")


if __name__ == "__main__":
    interactive_cli()
