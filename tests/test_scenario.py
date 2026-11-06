import json
import os
import tempfile
import unittest

from domain.deck import CyberDeck
from domain.graph import NetworkGraph
from domain.node import NetworkNode, NodeState
from domain.program import PortScanner
from domain.scenario import ScenarioLoader
from domain.session import GameSession
from domain.trace import TraceAcceleratorIce, TraceEngine
from ui.terminal import TerminalUI


class TestScenarioAndPersistence(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_scenario_dict = {
            "name": "Test Mission",
            "target_objective_ip": "10.0.0.2",
            "network": {
                "root_node": "10.0.0.1",
                "nodes": [
                    {
                        "ip": "10.0.0.1",
                        "hostname": "gw-01",
                        "security_level": 1,
                        "ports": {"80": False},
                        "state": "UNDISCOVERED",
                    },
                    {
                        "ip": "10.0.0.2",
                        "hostname": "vault-01",
                        "security_level": 2,
                        "ports": {"22": False},
                        "data_payload": "TOP_SECRET_PLANS",
                        "state": "UNDISCOVERED",
                    },
                ],
                "edges": [["10.0.0.1", "10.0.0.2"]],
            },
            "deck": {"total_ram": 8, "cpu_cores": 2},
            "trace": {
                "base_detection_rate": 3.0,
                "alert_threshold": 50.0,
                "ice": [
                    {
                        "type": "TraceAcceleratorIce",
                        "name": "SpeedAmp",
                        "trigger_threshold": 40.0,
                        "boost_rate": 2.0,
                    }
                ],
            },
        }

    def test_scenario_validation_errors(self) -> None:
        # Non-dict
        with self.assertRaises(TypeError):
            ScenarioLoader.validate_scenario_dict("not-a-dict")  # type: ignore

        # Missing required key
        invalid = dict(self.valid_scenario_dict)
        del invalid["target_objective_ip"]
        with self.assertRaises(KeyError):
            ScenarioLoader.validate_scenario_dict(invalid)

        # Invalid root node not in nodes
        invalid = json.loads(json.dumps(self.valid_scenario_dict))
        invalid["network"]["root_node"] = "99.99.99.99"
        with self.assertRaises(ValueError):
            ScenarioLoader.validate_scenario_dict(invalid)

        # Duplicate node IPs
        invalid = json.loads(json.dumps(self.valid_scenario_dict))
        invalid["network"]["nodes"].append(
            {"ip": "10.0.0.1", "hostname": "duplicate", "security_level": 1}
        )
        with self.assertRaises(ValueError):
            ScenarioLoader.validate_scenario_dict(invalid)

        # Invalid deck RAM
        invalid = json.loads(json.dumps(self.valid_scenario_dict))
        invalid["deck"]["total_ram"] = 0
        with self.assertRaises(ValueError):
            ScenarioLoader.validate_scenario_dict(invalid)

        # Invalid trace alert threshold
        invalid = json.loads(json.dumps(self.valid_scenario_dict))
        invalid["trace"]["alert_threshold"] = 150.0
        with self.assertRaises(ValueError):
            ScenarioLoader.validate_scenario_dict(invalid)

    def test_load_scenario_from_dict(self) -> None:
        session = ScenarioLoader.load_scenario_from_dict(self.valid_scenario_dict)
        self.assertEqual(len(session.graph.nodes), 2)
        self.assertEqual(session.graph.root_node, "10.0.0.1")
        self.assertEqual(session.target_objective_ip, "10.0.0.2")
        self.assertEqual(session.deck.total_ram, 8)
        self.assertEqual(session.deck.cpu_cores, 2)
        self.assertEqual(session.trace.base_detection_rate, 3.0)
        self.assertEqual(len(session.trace.active_ice), 1)

    def test_load_campaign_files_from_disk(self) -> None:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        iron_gate_path = os.path.join(base_dir, "scenarios", "operation_iron_gate.json")
        shadow_grid_path = os.path.join(base_dir, "scenarios", "shadow_grid.json")

        # Test Operation Iron Gate
        self.assertTrue(os.path.exists(iron_gate_path))
        session_iron = ScenarioLoader.load_scenario_from_file(iron_gate_path)
        self.assertEqual(len(session_iron.graph.nodes), 3)
        self.assertEqual(session_iron.target_objective_ip, "10.0.0.3")

        # Test Operation Shadow Grid
        self.assertTrue(os.path.exists(shadow_grid_path))
        session_shadow = ScenarioLoader.load_scenario_from_file(shadow_grid_path)
        self.assertEqual(len(session_shadow.graph.nodes), 5)
        self.assertEqual(session_shadow.target_objective_ip, "10.0.1.100")
        self.assertEqual(session_shadow.deck.total_ram, 12)

    def test_save_and_load_session_roundtrip(self) -> None:
        # Build initial session and advance progress
        session = ScenarioLoader.load_scenario_from_dict(self.valid_scenario_dict)
        scanner = session.deploy_scanner("10.0.0.1")
        session.tick()  # 1 tick into the 2-tick scanner (50% progress)
        self.assertEqual(session.turn, 1)
        self.assertEqual(scanner.progress, 50.0)
        self.assertEqual(len(session.deck.active_programs), 1)
        self.assertTrue(session.trace.trace_percentage > 0.0)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            ScenarioLoader.save_session_to_file(session, tmp_path)
            self.assertTrue(os.path.exists(tmp_path))

            # Resume session from saved file
            resumed = ScenarioLoader.load_session_from_file(tmp_path)
            self.assertEqual(resumed.turn, 1)
            self.assertEqual(len(resumed.deck.active_programs), 1)

            resumed_prog = resumed.deck.active_programs[0]
            self.assertEqual(resumed_prog.name, "PortScanner")
            self.assertEqual(resumed_prog.target_node.ip, "10.0.0.1")
            self.assertEqual(resumed_prog.progress, 50.0)
            self.assertEqual(resumed.trace.trace_percentage, session.trace.trace_percentage)

            # Advance the resumed session to completion
            resumed.tick()
            self.assertEqual(resumed.turn, 2)
            self.assertEqual(len(resumed.deck.active_programs), 0)
            self.assertEqual(resumed.graph.nodes["10.0.0.1"].state, NodeState.PROBED)

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_ui_save_and_load_commands(self) -> None:
        session = ScenarioLoader.load_scenario_from_dict(self.valid_scenario_dict)
        ui = TerminalUI(session, use_colors=False)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Save command
            save_out = ui.execute_command(f"save {tmp_path}")
            self.assertIn("Session successfully saved", save_out)

            # Modify state in UI
            ui.execute_command("scan 10.0.0.1")
            ui.execute_command("tick 1")
            self.assertEqual(ui.session.turn, 1)

            # Reload command resets to saved state
            load_out = ui.execute_command(f"load {tmp_path}")
            self.assertIn("Session successfully loaded", load_out)
            self.assertEqual(ui.session.turn, 0)

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()

