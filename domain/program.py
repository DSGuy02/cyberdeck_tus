from abc import ABC, abstractmethod
from typing import Dict, Optional

from .node import NetworkNode, NodeState


class BaseProgram(ABC):
    """Abstract base class representing an intrusion program executable on a CyberDeck."""

    def __init__(
        self,
        name: str,
        ram_cost: int,
        execution_time: int,
        target_node: NetworkNode,
    ) -> None:
        if not name or not name.strip():
            raise ValueError("Program name cannot be empty.")
        if ram_cost < 1:
            raise ValueError("RAM cost must be at least 1.")
        if execution_time < 1:
            raise ValueError("Execution time must be at least 1 tick.")
        if not isinstance(target_node, NetworkNode):
            raise TypeError("Target node must be an instance of NetworkNode.")

        self.name: str = name.strip()
        self.ram_cost: int = ram_cost
        self.execution_time: int = execution_time
        self.target_node: NetworkNode = target_node

        self.current_step: int = 0
        self.progress: float = 0.0
        self.is_complete: bool = False
        self.is_aborted: bool = False

    def execute_step(self) -> bool:
        """Advances execution by one step/tick. Returns True if execution completed."""
        if self.is_complete:
            return True
        if self.is_aborted:
            raise RuntimeError(f"Cannot execute aborted program {self.name}.")

        self.current_step += 1
        self.progress = min(100.0, (self.current_step / self.execution_time) * 100.0)

        if self.current_step >= self.execution_time:
            self.progress = 100.0
            self.is_complete = True
            self.on_complete()
            return True

        return False

    def abort(self) -> None:
        """Halts the program immediately and marks it as aborted."""
        if not self.is_complete:
            self.is_aborted = True

    @abstractmethod
    def on_complete(self) -> None:
        """Polymorphic completion hook triggered when progress reaches 100%."""
        pass


class PortScanner(BaseProgram):
    """Reconnaissance program that scans a target node to discover its ports and status."""

    def __init__(
        self,
        target_node: NetworkNode,
        ram_cost: int = 2,
        execution_time: int = 2,
    ) -> None:
        super().__init__(
            name="PortScanner",
            ram_cost=ram_cost,
            execution_time=execution_time,
            target_node=target_node,
        )
        self.discovered_ports: Dict[int, bool] = {}

    def on_complete(self) -> None:
        self.discovered_ports = self.target_node.probe_ports()


class BruteForcer(BaseProgram):
    """Exploitation program that cracks and opens a specific port on a target node."""

    def __init__(
        self,
        target_node: NetworkNode,
        target_port: int,
        ram_cost: int = 3,
        execution_time: Optional[int] = None,
    ) -> None:
        if not isinstance(target_port, int):
            raise TypeError("Target port must be an integer.")
        if target_node.ports and target_port not in target_node.ports:
            raise ValueError(f"Port {target_port} does not exist on target node {target_node.ip}.")

        # Execution time scales with node security level if not explicitly provided
        calc_time = execution_time if execution_time is not None else max(1, target_node.security_level * 2)

        super().__init__(
            name="BruteForcer",
            ram_cost=ram_cost,
            execution_time=calc_time,
            target_node=target_node,
        )
        self.target_port: int = target_port

    def on_complete(self) -> None:
        self.target_node.open_port(self.target_port)
        # Attempt firewall breach if all ports have been opened
        if self.target_node.ports and all(self.target_node.ports.values()):
            self.target_node.breach_firewall()


class DataExtractor(BaseProgram):
    """Payload program that exfiltrates data from an exploited target node."""

    def __init__(
        self,
        target_node: NetworkNode,
        ram_cost: int = 4,
        execution_time: int = 3,
    ) -> None:
        super().__init__(
            name="DataExtractor",
            ram_cost=ram_cost,
            execution_time=execution_time,
            target_node=target_node,
        )
        self.extracted_payload: Optional[str] = None

    def on_complete(self) -> None:
        if self.target_node.state != NodeState.EXPLOITED:
            raise PermissionError(
                f"Cannot extract data: target node {self.target_node.ip} is not exploited."
            )
        self.extracted_payload = self.target_node.extract_data()
