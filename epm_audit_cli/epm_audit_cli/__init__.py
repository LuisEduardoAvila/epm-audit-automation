"""
EPM Audit CLI

CLI for Oracle EPM Cloud audit and governance operations.
Provides artifact change tracking, EDM request history, business rule inspection,
and OCI infrastructure monitoring.
"""

__version__ = "0.1.0"
__author__ = "EPM Audit Team"

from epm_audit_cli.cli import cli

__all__ = ["cli"]