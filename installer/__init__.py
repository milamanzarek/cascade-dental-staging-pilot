"""
One-Click Windows Clinic Edge Installer for Lane 3 Healthcare AI.

Provides automated PowerShell service deployment, interactive setup wizard,
and pre-flight system diagnostics for clinic IT MSPs and non-technical staff.
"""

from .config_wizard import (
    ClinicConfig,
    PMSType,
    CarrierType,
    ConfigWizardEngine,
    run_preflight_checks
)

__all__ = [
    "ClinicConfig",
    "PMSType",
    "CarrierType",
    "ConfigWizardEngine",
    "run_preflight_checks"
]
