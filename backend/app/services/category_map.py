"""Mapping of student reported symptoms to fixed ProblemType enum categories.

Specification Section 5.3:
The problem type is a fixed list of five values:
LAN_PROBLEM, IP_ADDRESS_ISSUE, PROXY_ISSUE, LAN_PORT_BROKEN, WIFI_PROBLEM
"""

from typing import Dict, Optional
from backend.app.models import ProblemType

# Ordered by specificity (longer/more specific phrases first)
SYMPTOM_CATEGORY_MAP: Dict[str, ProblemType] = {
    # LAN PORT BROKEN
    "lan port": ProblemType.LAN_PORT_BROKEN,
    "wall socket": ProblemType.LAN_PORT_BROKEN,
    "socket": ProblemType.LAN_PORT_BROKEN,
    "cable fault": ProblemType.LAN_PORT_BROKEN,
    "connector": ProblemType.LAN_PORT_BROKEN,

    # WIFI PROBLEM
    "wifi": ProblemType.WIFI_PROBLEM,
    "wi-fi": ProblemType.WIFI_PROBLEM,
    "access point": ProblemType.WIFI_PROBLEM,
    "signal": ProblemType.WIFI_PROBLEM,
    "wireless": ProblemType.WIFI_PROBLEM,

    # IP ADDRESS ISSUE
    "ip address": ProblemType.IP_ADDRESS_ISSUE,
    "no ip": ProblemType.IP_ADDRESS_ISSUE,
    "dhcp": ProblemType.IP_ADDRESS_ISSUE,
    "dns": ProblemType.IP_ADDRESS_ISSUE,
    "ip": ProblemType.IP_ADDRESS_ISSUE,

    # PROXY ISSUE
    "proxy": ProblemType.PROXY_ISSUE,
    "port 8080": ProblemType.PROXY_ISSUE,
    "browser": ProblemType.PROXY_ISSUE,

    # LAN PROBLEM
    "slow internet": ProblemType.LAN_PROBLEM,
    "lan": ProblemType.LAN_PROBLEM,
    "wired": ProblemType.LAN_PROBLEM,
    "switch": ProblemType.LAN_PROBLEM,
    "vlan": ProblemType.LAN_PROBLEM,
}


def map_symptom_to_category(text: str) -> Optional[ProblemType]:
    """Scans message text for key symptoms and returns the matching ProblemType.

    Args:
        text: Student message or transcript text.

    Returns:
        ProblemType enum or None if no confident match.
    """
    text_lower = text.lower()
    for keyword, category in SYMPTOM_CATEGORY_MAP.items():
        if keyword in text_lower:
            return category
    return None
