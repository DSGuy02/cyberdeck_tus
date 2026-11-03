#!/usr/bin/env python3
"""CyberDeck - Gamified Network Infiltration & Intrusion Countermeasure Simulator.

Main entrypoint for running the interactive terminal simulation.
"""

from domain.deck import CyberDeck
from domain.graph import NetworkGraph
from domain.node import NetworkNode
from domain.session import GameSession
from domain.trace import FirewallLockIce, TraceAcceleratorIce, TraceEngine
from ui.terminal import TerminalUI


def build_default_scenario() -> GameSession:
    """Builds a realistic three-tier enterprise network scenario."""
    # 1. Create target machines
    gateway = NetworkNode(
        ip="10.0.0.1",
        hostname="gw-perimeter",
        security_level=1,
        ports={80: False},
    )
    proxy = NetworkNode(
        ip="10.0.0.2",
        hostname="proxy-internal",
        security_level=2,
        ports={22: False, 443: False},
    )
    vault = NetworkNode(
        ip="10.0.0.3",
        hostname="vault-database",
        security_level=3,
        ports={3306: False, 8080: False},
        data_payload="CONFIDENTIAL_CYBERDECK_SCHEMATICS_V4",
    )

    # 2. Build network graph topology
    graph = NetworkGraph()
    graph.add_node(gateway, is_root=True)
    graph.add_node(proxy)
    graph.add_node(vault)
    graph.connect("10.0.0.1", "10.0.0.2")
    graph.connect("10.0.0.2", "10.0.0.3")

    # 3. Configure hardware CyberDeck
    deck = CyberDeck(total_ram=8, cpu_cores=2)

    # 4. Configure defensive TraceEngine and ICE countermeasures
    trace = TraceEngine(base_detection_rate=2.5, alert_threshold=50.0)
    trace.add_ice(TraceAcceleratorIce(trigger_threshold=40.0, boost_rate=2.0))
    trace.add_ice(FirewallLockIce(target_node=vault, trigger_threshold=85.0))

    # 5. Create game session with target objective
    session = GameSession(
        graph=graph,
        deck=deck,
        trace=trace,
        target_objective_ip="10.0.0.3",
    )
    return session


def main() -> None:
    session = build_default_scenario()
    ui = TerminalUI(session=session, use_colors=True)
    ui.run_interactive_loop()


if __name__ == "__main__":
    main()
