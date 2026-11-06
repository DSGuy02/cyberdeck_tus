import json
import os
from typing import Any, Dict, List, Optional

from .deck import CyberDeck
from .graph import NetworkGraph
from .node import NetworkNode, NodeState
from .program import BaseProgram, BruteForcer, DataExtractor, PortScanner
from .session import GameSession
from .trace import BaseIceDaemon, FirewallLockIce, TraceAcceleratorIce, TraceEngine


class ScenarioLoader:
    """Handles loading, validation, and persistence of network scenarios and game sessions."""

    @staticmethod
    def validate_scenario_dict(data: Dict[str, Any]) -> None:
        """Validates that a dictionary contains all required fields and conforms to scenario schema."""
        if not isinstance(data, dict):
            raise TypeError("Scenario data must be a JSON dictionary.")

        required_keys = ["name", "target_objective_ip", "network", "deck", "trace"]
        for key in required_keys:
            if key not in data:
                raise KeyError(f"Missing required scenario configuration key: '{key}'.")

        # Validate network configuration
        net = data["network"]
        if not isinstance(net, dict):
            raise TypeError("'network' configuration must be a dictionary.")
        if "root_node" not in net or not net["root_node"]:
            raise ValueError("Network configuration must specify a non-empty 'root_node'.")
        if "nodes" not in net or not isinstance(net["nodes"], list) or not net["nodes"]:
            raise ValueError("Network configuration must include a non-empty 'nodes' list.")
        if "edges" not in net or not isinstance(net["edges"], list):
            raise ValueError("Network configuration must include an 'edges' list.")

        node_ips = set()
        for node_info in net["nodes"]:
            if "ip" not in node_info or not node_info["ip"].strip():
                raise ValueError("Every node must have a valid, non-empty 'ip'.")
            if "hostname" not in node_info or not node_info["hostname"].strip():
                raise ValueError("Every node must have a valid, non-empty 'hostname'.")
            ip = node_info["ip"].strip()
            if ip in node_ips:
                raise ValueError(f"Duplicate node IP address '{ip}' detected in scenario.")
            node_ips.add(ip)

        if net["root_node"] not in node_ips:
            raise ValueError(f"Root node IP '{net['root_node']}' does not exist in nodes list.")

        if data["target_objective_ip"] not in node_ips:
            raise ValueError(
                f"Target objective IP '{data['target_objective_ip']}' does not exist in nodes list."
            )

        # Validate hardware deck configuration
        deck_info = data["deck"]
        if not isinstance(deck_info, dict):
            raise TypeError("'deck' configuration must be a dictionary.")
        if deck_info.get("total_ram", 0) < 1:
            raise ValueError("CyberDeck 'total_ram' must be at least 1.")
        if deck_info.get("cpu_cores", 0) < 1:
            raise ValueError("CyberDeck 'cpu_cores' must be at least 1.")

        # Validate defensive trace configuration
        trace_info = data["trace"]
        if not isinstance(trace_info, dict):
            raise TypeError("'trace' configuration must be a dictionary.")
        if trace_info.get("base_detection_rate", 0.0) <= 0.0:
            raise ValueError("Trace 'base_detection_rate' must be greater than zero.")
        alert_thresh = trace_info.get("alert_threshold", 50.0)
        if not (1.0 <= alert_thresh < 100.0):
            raise ValueError("Trace 'alert_threshold' must be between 1.0 and 99.0.")

    @classmethod
    def load_scenario_from_dict(cls, data: Dict[str, Any]) -> GameSession:
        """Constructs a fully configured GameSession from a validated scenario dictionary."""
        cls.validate_scenario_dict(data)

        # 1. Build Network Nodes
        graph = NetworkGraph()
        nodes_map: Dict[str, NetworkNode] = {}
        net_info = data["network"]

        for item in net_info["nodes"]:
            ip = item["ip"].strip()
            hostname = item["hostname"].strip()
            sec_lvl = int(item.get("security_level", 1))
            ports_raw = item.get("ports", {})
            # Ensure port numbers are integers
            ports = {int(p): bool(status) for p, status in ports_raw.items()}
            payload = item.get("data_payload")
            state_str = item.get("state", "UNDISCOVERED")
            state = NodeState[state_str] if state_str in NodeState.__members__ else NodeState.UNDISCOVERED

            node = NetworkNode(
                ip=ip,
                hostname=hostname,
                security_level=sec_lvl,
                ports=ports,
                data_payload=payload,
                state=state,
            )
            is_root = ip == net_info["root_node"]
            graph.add_node(node, is_root=is_root)
            nodes_map[ip] = node

        # 2. Build Connections
        for edge in net_info.get("edges", []):
            if len(edge) >= 2:
                src, dst = edge[0], edge[1]
                graph.connect(src, dst)

        # 3. Build CyberDeck
        deck_info = data["deck"]
        deck = CyberDeck(
            total_ram=int(deck_info.get("total_ram", 8)),
            cpu_cores=int(deck_info.get("cpu_cores", 2)),
        )

        # 4. Build TraceEngine and ICE daemons
        trace_info = data["trace"]
        trace = TraceEngine(
            base_detection_rate=float(trace_info.get("base_detection_rate", 2.5)),
            alert_threshold=float(trace_info.get("alert_threshold", 50.0)),
        )

        for ice_item in trace_info.get("ice", []):
            ice_type = ice_item.get("type")
            ice_name = ice_item.get("name", "DefensiveICE")
            threshold = float(ice_item.get("trigger_threshold", 50.0))

            if ice_type == "TraceAcceleratorIce":
                boost = float(ice_item.get("boost_rate", 2.0))
                ice_daemon = TraceAcceleratorIce(name=ice_name, trigger_threshold=threshold, boost_rate=boost)
                trace.add_ice(ice_daemon)
            elif ice_type == "FirewallLockIce":
                target_ip = ice_item.get("target_ip")
                if target_ip and target_ip in nodes_map:
                    ice_daemon = FirewallLockIce(
                        target_node=nodes_map[target_ip],
                        name=ice_name,
                        trigger_threshold=threshold,
                    )
                    trace.add_ice(ice_daemon)

        # 5. Build and return Session
        session = GameSession(
            graph=graph,
            deck=deck,
            trace=trace,
            target_objective_ip=data.get("target_objective_ip"),
        )
        return session

    @classmethod
    def load_scenario_from_file(cls, filepath: str) -> GameSession:
        """Reads a JSON scenario file from disk and initialises a GameSession."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Scenario file '{filepath}' does not exist.")

        with open(filepath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as err:
                raise ValueError(f"Malformed scenario JSON in '{filepath}': {err}")

        return cls.load_scenario_from_dict(data)

    @staticmethod
    def save_session_to_file(session: GameSession, filepath: str) -> None:
        """Serialises the complete live GameSession state to a JSON file."""
        if not isinstance(session, GameSession):
            raise TypeError("Expected an instance of GameSession.")

        # Serialize NetworkGraph
        network_data = {
            "root_node": session.graph.root_node,
            "nodes": [
                {
                    "ip": node.ip,
                    "hostname": node.hostname,
                    "security_level": node.security_level,
                    "ports": {str(p): status for p, status in node.ports.items()},
                    "data_payload": node.data_payload,
                    "state": node.state.value,
                }
                for node in session.graph.nodes.values()
            ],
            "edges": list(session.graph.edges),
        }

        # Serialize Active Programs on Deck
        active_programs_data = []
        for prog in session.deck.active_programs:
            prog_dict: Dict[str, Any] = {
                "type": prog.__class__.__name__,
                "name": prog.name,
                "target_ip": prog.target_node.ip,
                "ram_cost": prog.ram_cost,
                "execution_time": prog.execution_time,
                "current_step": prog.current_step,
                "progress": prog.progress,
            }
            if isinstance(prog, BruteForcer):
                prog_dict["target_port"] = prog.target_port
            active_programs_data.append(prog_dict)

        deck_data = {
            "total_ram": session.deck.total_ram,
            "used_ram": session.deck.used_ram,
            "cpu_cores": session.deck.cpu_cores,
            "active_programs": active_programs_data,
        }

        # Serialize TraceEngine and ICE
        ice_data = []
        for daemon in session.trace.active_ice:
            daemon_dict: Dict[str, Any] = {
                "type": daemon.__class__.__name__,
                "name": daemon.name,
                "trigger_threshold": daemon.trigger_threshold,
                "is_active": daemon.is_active,
            }
            if isinstance(daemon, TraceAcceleratorIce):
                daemon_dict["boost_rate"] = daemon.boost_rate
                daemon_dict["applied"] = daemon.applied
            elif isinstance(daemon, FirewallLockIce):
                daemon_dict["target_ip"] = daemon.target_node.ip
                daemon_dict["has_triggered"] = daemon.has_triggered
            ice_data.append(daemon_dict)

        trace_data = {
            "trace_percentage": session.trace.trace_percentage,
            "base_detection_rate": session.trace.base_detection_rate,
            "detection_rate": session.trace.detection_rate,
            "alert_threshold": session.trace.alert_threshold,
            "is_alerted": session.trace.is_alerted,
            "is_game_over": session.trace.is_game_over,
            "ice": ice_data,
        }

        save_dict = {
            "version": "1.0",
            "turn": session.turn,
            "target_objective_ip": session.target_objective_ip,
            "is_victory": session.is_victory,
            "exfiltrated_data": list(session.exfiltrated_data),
            "event_log": list(session.event_log),
            "network": network_data,
            "deck": deck_data,
            "trace": trace_data,
        }

        # Write to disk
        parent_dir = os.path.dirname(filepath)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(save_dict, f, indent=2)

    @classmethod
    def load_session_from_file(cls, filepath: str) -> GameSession:
        """Reconstructs a live GameSession with exact progress from a saved JSON file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Save file '{filepath}' does not exist.")

        with open(filepath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as err:
                raise ValueError(f"Malformed savegame JSON in '{filepath}': {err}")

        # 1. Rebuild Network
        graph = NetworkGraph()
        nodes_map: Dict[str, NetworkNode] = {}
        net_info = data["network"]

        for item in net_info["nodes"]:
            ip = item["ip"]
            ports = {int(p): bool(st) for p, st in item.get("ports", {}).items()}
            node = NetworkNode(
                ip=ip,
                hostname=item["hostname"],
                security_level=int(item["security_level"]),
                ports=ports,
                data_payload=item.get("data_payload"),
                state=NodeState[item["state"]],
            )
            is_root = ip == net_info.get("root_node")
            graph.add_node(node, is_root=is_root)
            nodes_map[ip] = node

        for edge in net_info.get("edges", []):
            if len(edge) >= 2:
                graph.connect(edge[0], edge[1])

        # 2. Rebuild CyberDeck
        deck_info = data["deck"]
        deck = CyberDeck(
            total_ram=int(deck_info["total_ram"]),
            cpu_cores=int(deck_info["cpu_cores"]),
        )

        for prog_item in deck_info.get("active_programs", []):
            target_ip = prog_item["target_ip"]
            target_node = nodes_map[target_ip]
            prog_type = prog_item["type"]

            program: BaseProgram
            if prog_type == "PortScanner":
                program = PortScanner(
                    target_node=target_node,
                    ram_cost=int(prog_item["ram_cost"]),
                    execution_time=int(prog_item["execution_time"]),
                )
            elif prog_type == "BruteForcer":
                program = BruteForcer(
                    target_node=target_node,
                    target_port=int(prog_item["target_port"]),
                    ram_cost=int(prog_item["ram_cost"]),
                    execution_time=int(prog_item["execution_time"]),
                )
            elif prog_type == "DataExtractor":
                program = DataExtractor(
                    target_node=target_node,
                    ram_cost=int(prog_item["ram_cost"]),
                    execution_time=int(prog_item["execution_time"]),
                )
            else:
                continue

            program.current_step = int(prog_item.get("current_step", 0))
            program.progress = float(prog_item.get("progress", 0.0))
            deck.load_program(program)

        # 3. Rebuild TraceEngine and ICE
        trace_info = data["trace"]
        trace = TraceEngine(
            base_detection_rate=float(trace_info.get("base_detection_rate", 2.0)),
            alert_threshold=float(trace_info.get("alert_threshold", 50.0)),
        )
        trace.trace_percentage = float(trace_info.get("trace_percentage", 0.0))
        trace.detection_rate = float(trace_info.get("detection_rate", trace.base_detection_rate))
        trace.is_alerted = bool(trace_info.get("is_alerted", False))
        trace.is_game_over = bool(trace_info.get("is_game_over", False))

        for ice_item in trace_info.get("ice", []):
            ice_type = ice_item.get("type")
            ice_name = ice_item.get("name", "DefensiveICE")
            threshold = float(ice_item.get("trigger_threshold", 50.0))

            if ice_type == "TraceAcceleratorIce":
                accel_ice = TraceAcceleratorIce(
                    name=ice_name,
                    trigger_threshold=threshold,
                    boost_rate=float(ice_item.get("boost_rate", 2.0)),
                )
                accel_ice.is_active = bool(ice_item.get("is_active", False))
                accel_ice.applied = bool(ice_item.get("applied", False))
                trace.add_ice(accel_ice)
            elif ice_type == "FirewallLockIce":
                target_ip = ice_item.get("target_ip")
                if target_ip and target_ip in nodes_map:
                    lock_ice = FirewallLockIce(
                        target_node=nodes_map[target_ip],
                        name=ice_name,
                        trigger_threshold=threshold,
                    )
                    lock_ice.is_active = bool(ice_item.get("is_active", False))
                    lock_ice.has_triggered = bool(ice_item.get("has_triggered", False))
                    trace.add_ice(lock_ice)

        # 4. Rebuild GameSession
        session = GameSession(
            graph=graph,
            deck=deck,
            trace=trace,
            target_objective_ip=data.get("target_objective_ip"),
        )
        session.turn = int(data.get("turn", 0))
        session.is_victory = bool(data.get("is_victory", False))
        session.exfiltrated_data = list(data.get("exfiltrated_data", []))
        session.event_log = list(data.get("event_log", []))

        return session

