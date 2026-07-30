"""Endpoint security tools for device and malware operations."""

from src.tools.common import find_mock_record, filter_mock_records, load_mock_data


def check_endpoint_status(device_id: str) -> dict:
    """Check health status and last check-in for an endpoint."""
    devices = load_mock_data("mock_devices.json")
    device = find_mock_record(devices, "device_id", device_id)

    if not device:
        return {"error": "Device not found", "device_id": device_id}

    return {
        "device_id": device_id,
        "hostname": device.get("hostname"),
        "ip_address": device.get("ip_address"),
        "status": device.get("status"),
        "last_checkin": device.get("last_checkin"),
    }


def search_device(name_or_ip: str) -> list[dict]:
    """Find devices by hostname or IP address."""
    devices = load_mock_data("mock_devices.json")

    results = [
        d
        for d in devices
        if name_or_ip.lower() in d.get("hostname", "").lower()
        or name_or_ip in d.get("ip_address", "")
    ]

    return results


def scan_device(device_id: str) -> dict:
    """Scan device for malware (requires human approval)."""
    return {
        "device_id": device_id,
        "scan_status": "initiated",
        "message": f"Malware scan started for device {device_id}",
        "timestamp": "2025-07-30T10:45:00Z",
    }


def get_malware_details(device_id: str) -> list[dict]:
    """Get list of detected malware on a device."""
    devices = load_mock_data("mock_devices.json")
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
