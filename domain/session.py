from typing import List, Optional

from .deck import CyberDeck
from .graph import NetworkGraph
from .node import NetworkNode, NodeState
from .program import BaseProgram, BruteForcer, DataExtractor, PortScanner
from .trace import TraceEngine


class GameSession:
    """Coordinates the simulation state, managing the network, deck, trace, and game rules."""

    def __init__(
        self,
        graph: NetworkGraph,
        deck: CyberDeck,
        trace: TraceEngine,
        target_objective_ip: Optional[str] = None,
    ) -> None:
        if not isinstance(graph, NetworkGraph):
            raise TypeError("Expected an instance of NetworkGraph.")
        if not isinstance(deck, CyberDeck):
            raise TypeError("Expected an instance of CyberDeck.")
        if not isinstance(trace, TraceEngine):
            raise TypeError("Expected an instance of TraceEngine.")

        self.graph: NetworkGraph = graph
        self.deck: CyberDeck = deck
        self.trace: TraceEngine = trace
        self.target_objective_ip: Optional[str] = target_objective_ip

        self.turn: int = 0
        self.event_log: List[str] = []
        self.exfiltrated_data: List[str] = []
        self.is_victory: bool = False

        self.log_event("Simulation session initialised. Ready for infiltration commands.")

    def log_event(self, message: str) -> None:
        """Records an event with a simulation turn timestamp."""
        entry = f"[Turn {self.turn:02d}] {message}"
        self.event_log.append(entry)

    @property
    def is_game_over(self) -> bool:
        """Returns True if the defensive trace reached 100%."""
        return self.trace.is_game_over

    @property
    def is_finished(self) -> bool:
        """Returns True if the mission has ended in victory or defeat."""
        return self.is_victory or self.is_game_over

    def deploy_scanner(self, target_ip: str) -> PortScanner:
        """Deploys a PortScanner against a reachable network node."""
        if self.is_finished:
            raise RuntimeError("Cannot deploy programs: session is already concluded.")
        if target_ip not in self.graph.nodes:
            raise KeyError(f"Target node {target_ip} does not exist in the network.")
        if not self.graph.is_reachable(target_ip):
            raise PermissionError(f"Node {target_ip} is unreachable from current pivot points.")

        target_node = self.graph.nodes[target_ip]
        scanner = PortScanner(target_node=target_node)
        self.deck.load_program(scanner)
        self.log_event(f"Deployed PortScanner on {target_node.hostname} ({target_ip}).")
        return scanner

    def deploy_brute_forcer(self, target_ip: str, target_port: int) -> BruteForcer:
        """Deploys a BruteForcer to crack a specific port on a probed node."""
        if self.is_finished:
            raise RuntimeError("Cannot deploy programs: session is already concluded.")
        if target_ip not in self.graph.nodes:
            raise KeyError(f"Target node {target_ip} does not exist in the network.")
        if not self.graph.is_reachable(target_ip):
            raise PermissionError(f"Node {target_ip} is unreachable from current pivot points.")

        target_node = self.graph.nodes[target_ip]
        if target_node.state == NodeState.UNDISCOVERED:
            raise PermissionError(f"Node {target_ip} must be probed before cracking ports.")

        cracker = BruteForcer(target_node=target_node, target_port=target_port)
        self.deck.load_program(cracker)
        self.log_event(
            f"Deployed BruteForcer against port {target_port} on {target_node.hostname} ({target_ip})."
        )
        return cracker

    def deploy_extractor(self, target_ip: str) -> DataExtractor:
        """Deploys a DataExtractor against an exploited node to steal confidential files."""
        if self.is_finished:
            raise RuntimeError("Cannot deploy programs: session is already concluded.")
        if target_ip not in self.graph.nodes:
            raise KeyError(f"Target node {target_ip} does not exist in the network.")
        if not self.graph.is_reachable(target_ip):
            raise PermissionError(f"Node {target_ip} is unreachable from current pivot points.")

        target_node = self.graph.nodes[target_ip]
        if target_node.state != NodeState.EXPLOITED:
            raise PermissionError(f"Cannot extract data: node {target_ip} has not been exploited.")

        extractor = DataExtractor(target_node=target_node)
        self.deck.load_program(extractor)
        self.log_event(f"Deployed DataExtractor on {target_node.hostname} ({target_ip}).")
        return extractor

    def abort_program_by_name(self, program_name: str) -> bool:
        """Aborts an active program matching the given name or target IP."""
        for prog in list(self.deck.active_programs):
            if prog.name.lower() == program_name.lower() or prog.target_node.ip == program_name:
                self.deck.abort_program(prog)
                self.log_event(f"Aborted program {prog.name} targeting {prog.target_node.ip}.")
                return True
        return False

    def tick(self) -> None:
        """Advances the simulation by one turn, updating the deck, trace, and win/loss rules."""
        if self.is_finished:
            return

        self.turn += 1

        # Advance all hardware programs
        completed_programs = self.deck.tick_all()

        for prog in completed_programs:
            if isinstance(prog, PortScanner):
                open_count = sum(1 for status in prog.discovered_ports.values() if status)
                self.log_event(
                    f"[COMPLETE] PortScanner on {prog.target_node.hostname} finished. "
                    f"Found {len(prog.discovered_ports)} ports ({open_count} open)."
                )
            elif isinstance(prog, BruteForcer):
                if prog.target_node.state == NodeState.EXPLOITED:
                    self.log_event(
                        f"[BREACH] Port {prog.target_port} cracked! Firewall breached on {prog.target_node.hostname}!"
                    )
                else:
                    self.log_event(
                        f"[COMPLETE] Port {prog.target_port} cracked open on {prog.target_node.hostname}."
                    )
            elif isinstance(prog, DataExtractor):
                if prog.extracted_payload:
                    self.exfiltrated_data.append(prog.extracted_payload)
                    self.log_event(
                        f"[DATA EXFILTRATED] Stolen payload from {prog.target_node.hostname}: {prog.extracted_payload}"
                    )
                    if self.target_objective_ip and prog.target_node.ip == self.target_objective_ip:
                        self.is_victory = True
                        self.log_event(
                            "[MISSION VICTORY] Target objective payload successfully secured! Infiltration complete!"
                        )

        # Advance defensive trace
        alert_before = self.trace.is_alerted
        self.trace.tick(deck=self.deck)

        if not alert_before and self.trace.is_alerted:
            self.log_event(
                f"[DEFENSE ALERT] Intrusion detection alarm triggered at {self.trace.trace_percentage:.1f}% trace!"
            )

        if self.trace.is_game_over:
            self.log_event(
                "[MISSION FAILED] Trace saturated at 100%! Cyberdeck connection severed by defensive ICE."
            )
