"""
safety.py
---------
Guardrail that every simulation target must pass through. Only loopback
(127.0.0.1) or addresses explicitly whitelisted in config.LAB_TARGETS
(which must themselves be private/RFC1918) are ever allowed.
"""
import ipaddress

from config import LAB_TARGETS

PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
]


def is_safe_target(target_ip):
    """Return True/False. Kept for backward compatibility with existing
    callers/tests that just want a boolean."""
    ok, _reason = check_target(target_ip)
    return ok


def check_target(target_ip):
    """Return (is_safe: bool, reason: str). The reason is always populated
    (even on success) so callers can surface it in logs or error responses."""
    try:
        ip = ipaddress.ip_address(target_ip)
    except (ValueError, TypeError):
        return False, f"'{target_ip}' is not a valid IP address."

    if str(ip) == "127.0.0.1":
        return True, "loopback address"

    is_private = any(ip in net for net in PRIVATE_NETWORKS)
    is_whitelisted = str(ip) in LAB_TARGETS

    if is_private and is_whitelisted:
        return True, "whitelisted private lab address"

    return False, (
        f"'{target_ip}' is not permitted. Only 127.0.0.1 or addresses "
        f"explicitly added to LAB_TARGETS in config.py (and within a "
        f"private/RFC1918 range) may be used as simulation targets."
    )
