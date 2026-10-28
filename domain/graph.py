from collections import deque
from typing import Any, Dict, List, Optional, Tuple

from .node import NetworkNode, NodeState


class NetworkGraph:
    """Manages network topology, node connections, and subnet reachability."""

    def __init__(self) -> None:
        self.nodes: Dict[str, NetworkNode] = {}
        self.edges: List[Tuple[str, str]] = []
        self.root_node: Optional[str] = None

    def add_node(self, node: NetworkNode, is_root: bool = False) -> None:
        if not isinstance(node, NetworkNode):
            raise TypeError("Expected a NetworkNode instance.")
        if node.ip in self.nodes:
            raise ValueError(f"Node with IP {node.ip} already exists in the graph.")

        self.nodes[node.ip] = node
        if is_root or self.root_node is None:
            self.root_node = node.ip

    def connect(self, source_ip: str, target_ip: str, bidirectional: bool = True) -> None:
        if source_ip not in self.nodes:
            raise KeyError(f"Source node {source_ip} does not exist.")
        if target_ip not in self.nodes:
            raise KeyError(f"Target node {target_ip} does not exist.")
        if source_ip == target_ip:
            raise ValueError("Cannot connect a node to itself.")

        if (source_ip, target_ip) not in self.edges:
            self.edges.append((source_ip, target_ip))

        if bidirectional and (target_ip, source_ip) not in self.edges:
            self.edges.append((target_ip, source_ip))

    def get_adjacent(self, ip: str) -> List[NetworkNode]:
        if ip not in self.nodes:
            raise KeyError(f"Node {ip} does not exist.")

        adjacent_ips = [target for source, target in self.edges if source == ip]
        return [self.nodes[adj_ip] for adj_ip in adjacent_ips]

    def is_reachable(self, target_ip: str) -> bool:
        if target_ip not in self.nodes:
            raise KeyError(f"Target node {target_ip} does not exist.")
        if self.root_node is None:
            return False
        if target_ip == self.root_node:
            return True

        visited = {self.root_node}
        queue = deque([self.root_node])

        while queue:
            current_ip = queue.popleft()
            current_node = self.nodes[current_ip]

            if current_node.state != NodeState.EXPLOITED:
                continue

            for neighbour in self.get_adjacent(current_ip):
                if neighbour.ip == target_ip:
                    return True
                if neighbour.ip not in visited:
                    visited.add(neighbour.ip)
                    queue.append(neighbour.ip)

        return False

    def serialize(self) -> Dict[str, Any]:
        return {
            "root_node": self.root_node,
            "nodes": {
                ip: {
                    "ip": node.ip,
                    "hostname": node.hostname,
                    "security_level": node.security_level,
                    "state": node.state.value,
                    "ports": dict(node.ports),
                    "data_payload": node.data_payload,
                }
                for ip, node in self.nodes.items()
            },
            "edges": list(self.edges),
        }
