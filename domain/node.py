from enum import Enum
from typing import Dict, Optional


class NodeState(Enum):
    UNDISCOVERED = "UNDISCOVERED"
    PROBED = "PROBED"
    EXPLOITED = "EXPLOITED"
    LOCKED = "LOCKED"


class NetworkNode:
    """Represents a target machine or server within a simulated network."""

    def __init__(
        self,
        ip: str,
        hostname: str,
        security_level: int = 1,
        ports: Optional[Dict[int, bool]] = None,
        data_payload: Optional[str] = None,
        state: NodeState = NodeState.UNDISCOVERED,
    ) -> None:
        if not ip or not ip.strip():
            raise ValueError("IP address cannot be empty.")
        if not hostname or not hostname.strip():
            raise ValueError("Hostname cannot be empty.")
        if security_level < 1:
            raise ValueError("Security level must be at least 1.")

        self.ip: str = ip.strip()
        self.hostname: str = hostname.strip()
        self.security_level: int = security_level
        self.state: NodeState = state
        self.ports: Dict[int, bool] = dict(ports) if ports is not None else {}
        self.data_payload: Optional[str] = data_payload

    def probe_ports(self) -> Dict[int, bool]:
        if self.state == NodeState.LOCKED:
            raise PermissionError(f"Node {self.ip} is locked and cannot be probed.")

        if self.state == NodeState.UNDISCOVERED:
            self.state = NodeState.PROBED

        return dict(self.ports)

    def open_port(self, port: int) -> bool:
        if self.state in (NodeState.UNDISCOVERED, NodeState.LOCKED):
            return False
        if port not in self.ports:
            return False

        self.ports[port] = True
        return True

    def breach_firewall(self) -> bool:
        if self.state in (NodeState.UNDISCOVERED, NodeState.LOCKED):
            return False
        if self.ports and not all(self.ports.values()):
            return False

        self.state = NodeState.EXPLOITED
        return True

    def extract_data(self) -> Optional[str]:
        if self.state != NodeState.EXPLOITED:
            raise PermissionError(f"Cannot extract data: node {self.ip} is not exploited.")

        payload = self.data_payload
        self.data_payload = None
        return payload

    def lock_node(self) -> None:
        self.state = NodeState.LOCKED
        for port in self.ports:
            self.ports[port] = False
