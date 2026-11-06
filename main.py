#!/usr/bin/env python3
"""CyberDeck - Gamified Network Infiltration & Intrusion Countermeasure Simulator.

Main entrypoint for running the interactive terminal simulation.
"""

import argparse
import os
import sys

from domain.deck import CyberDeck
from domain.graph import NetworkGraph
from domain.node import NetworkNode
from domain.scenario import ScenarioLoader
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


def resolve_default_scenario_path() -> str:
    """Finds the default scenario file path across working directory variations."""
    candidates = [
        os.path.join(os.path.dirname(__file__), "scenarios", "operation_iron_gate.json"),
        os.path.join("scenarios", "operation_iron_gate.json"),
        os.path.join("cyberdeck", "scenarios", "operation_iron_gate.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CyberDeck - Gamified Network Infiltration & Intrusion Countermeasure Simulator."
    )
    parser.add_argument(
        "scenario",
        nargs="?",
        default=None,
        help="Optional path to a custom JSON scenario file.",
    )
    parser.add_argument(
        "--scenario",
        dest="scenario_opt",
        default=None,
        help="Path to a custom JSON scenario file.",
    )
    parser.add_argument(
        "--load",
        dest="load_save",
        default=None,
        help="Path to a savegame file to resume an existing session.",
    )
    parser.add_argument(
        "--no-color",
        dest="no_color",
        action="store_true",
        help="Disable ANSI colors in terminal HUD.",
    )

    args = parser.parse_args()

    session: GameSession

    if args.load_save:
        try:
            session = ScenarioLoader.load_session_from_file(args.load_save)
            print(f"[CyberDeck] Resuming session loaded from '{args.load_save}'.")
        except Exception as err:
            print(f"[ERROR] Failed to load savegame '{args.load_save}': {err}", file=sys.stderr)
            sys.exit(1)
    else:
        target_scenario = args.scenario_opt or args.scenario or resolve_default_scenario_path()
        if target_scenario and os.path.exists(target_scenario):
            try:
                session = ScenarioLoader.load_scenario_from_file(target_scenario)
                print(f"[CyberDeck] Loaded mission scenario from '{target_scenario}'.")
            except Exception as err:
                print(f"[WARNING] Failed loading '{target_scenario}': {err}. Using default scenario.", file=sys.stderr)
                session = build_default_scenario()
        else:
            session = build_default_scenario()

    ui = TerminalUI(session=session, use_colors=not args.no_color)
    ui.run_interactive_loop()


if __name__ == "__main__":
    main()
