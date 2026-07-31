"""Endpoint security tools for device and malware operations."""

from datetime import datetime, timezone

from src.tools.common import find_mock_record
from src.tools.mock_store import load_records, update_record

DEVICES_FILE = "mock_devices.json"


def _now() -> str:
    """Current UTC time as an ISO-8601 Z timestamp, matching the mock data format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def check_endpoint_status(device_id: str) -> dict:
    """Check health status and last check-in for an endpoint.

    Reflects any scan that has already been approved.
    """
    devices = load_records(DEVICES_FILE)
    device = find_mock_record(devices, "device_id", device_id)

    if not device:
        return {"error": "Device not found", "device_id": device_id}

    return {
        "device_id": device_id,
        "hostname": device.get("hostname"),
        "ip_address": device.get("ip_address"),
        "status": device.get("status"),
        "last_checkin": device.get("last_checkin"),
        "last_scan_status": device.get("last_scan_status"),
        "last_scan_at": device.get("last_scan_at"),
    }


def search_device(name_or_ip: str) -> list[dict]:
    """Find devices by hostname or IP address."""
    devices = load_records(DEVICES_FILE)

    results = [
        d
        for d in devices
        if name_or_ip.lower() in d.get("hostname", "").lower()
        or name_or_ip in d.get("ip_address", "")
    ]

    return results


def scan_device(device_id: str) -> dict:
    """Scan device for malware (requires human approval).

    Writes the scan status, so a later status check reports it.
    """
    devices = load_records(DEVICES_FILE)

    if not find_mock_record(devices, "device_id", device_id):
        return {"error": "Device not found", "device_id": device_id}

    started_at = _now()

    updated = update_record(
        DEVICES_FILE,
        "device_id",
        device_id,
        {"last_scan_status": "initiated", "last_scan_at": started_at},
    )

    if updated is None:
        return {"error": "Could not record the scan", "device_id": device_id}

    return {
        "device_id": device_id,
        "scan_status": "initiated",
        "message": f"Malware scan started for device {device_id}",
        "timestamp": started_at,
    }


def get_malware_details(device_id: str) -> list[dict]:
    """Get list of detected malware on a device."""
    devices = load_records(DEVICES_FILE)
    device = find_mock_record(devices, "device_id", device_id)

    if not device or device.get("malware_count", 0) == 0:
        return []

    return [
        {
            "device_id": device_id,
            "malware_name": "Trojan.Win32.Generic",
            "severity": "HIGH",
            "detected": "2025-07-30T09:00:00Z",
        },
        {
            "device_id": device_id,
            "malware_name": "PUP.Optional.Adware",
            "severity": "LOW",
            "detected": "2025-07-30T08:30:00Z",
        },
    ]
