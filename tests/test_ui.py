import unittest
from typing import List

from domain.deck import CyberDeck
from domain.graph import NetworkGraph
from domain.node import NetworkNode
from domain.session import GameSession
from domain.trace import TraceEngine
from ui.terminal import TerminalUI


class TestTerminalUI(unittest.TestCase):
    def setUp(self) -> None:
        self.node = NetworkNode(ip="10.0.0.1", hostname="gw-01", security_level=1, ports={80: False})
        self.graph = NetworkGraph()
        self.graph.add_node(self.node, is_root=True)
        self.deck = CyberDeck(total_ram=8, cpu_cores=2)
        self.trace = TraceEngine(base_detection_rate=3.0, alert_threshold=50.0)
        self.session = GameSession(self.graph, self.deck, self.trace)
        self.ui = TerminalUI(self.session, use_colors=False)

    def test_ui_initialization_and_validation(self) -> None:
        self.assertFalse(self.ui.use_colors)
        with self.assertRaises(TypeError):
            TerminalUI("invalid-session")  # type: ignore

    def test_render_bar_utility(self) -> None:
        empty = self.ui.render_bar(0, 10, width=10)
        self.assertEqual(empty, "░" * 10)

        half = self.ui.render_bar(5, 10, width=10)
        self.assertEqual(half, "█" * 5 + "░" * 5)

        full = self.ui.render_bar(10, 10, width=10)
        self.assertEqual(full, "█" * 10)

    def test_render_dashboard_sections(self) -> None:
        dashboard = self.ui.render_dashboard()
        self.assertIn("CYBERDECK v1.0 // TERMINAL INFILTRATION HUD", dashboard)
        self.assertIn("TELEMETRY", dashboard)
        self.assertIn("NETWORK TOPOLOGY", dashboard)
        self.assertIn("ACTIVE CYBERDECK INTRUSION PROGRAMS", dashboard)
        self.assertIn("INFILTRATION EVENT LOG", dashboard)
        self.assertIn("10.0.0.1", dashboard)
        self.assertIn("gw-01", dashboard)

    def test_execute_command_help_and_status(self) -> None:
        help_out = self.ui.execute_command("help")
        self.assertIn("Available Commands:", help_out)
        self.assertIn("scan <ip>", help_out)

        status_out = self.ui.execute_command("status")
        self.assertEqual(status_out, "Telemetry refreshed.")

        empty_out = self.ui.execute_command("   ")
        self.assertEqual(empty_out, "")

    def test_execute_command_scan_and_tick(self) -> None:
        # Invalid scan usage
        err_out = self.ui.execute_command("scan")
        self.assertIn("[ERROR] Usage: scan <ip>", err_out)

        # Valid scan
        res = self.ui.execute_command("scan 10.0.0.1")
        self.assertIn("PortScanner successfully queued for 10.0.0.1", res)
        self.assertEqual(len(self.deck.active_programs), 1)

        # Tick command
        tick_res = self.ui.execute_command("tick 2")
        self.assertIn("Advanced simulation by 2 turn(s)", tick_res)
        self.assertEqual(self.session.turn, 2)
        # PortScanner takes 2 ticks -> now node is PROBED
        self.assertEqual(self.node.ports, {80: False})

    def test_execute_command_crack_and_extract_errors(self) -> None:
        # Crack usage error
        err1 = self.ui.execute_command("crack 10.0.0.1")
        self.assertIn("[ERROR] Usage: crack <ip> <port>", err1)

        # Crack invalid port
        err2 = self.ui.execute_command("crack 10.0.0.1 9999")
        self.assertIn("[ERROR]", err2)

        # Extract usage error
        err3 = self.ui.execute_command("extract")
        self.assertIn("[ERROR] Usage: extract <ip>", err3)

        # Extract on unexploited node
        err4 = self.ui.execute_command("extract 10.0.0.1")
        self.assertIn("[ERROR]", err4)

    def test_execute_command_abort(self) -> None:
        # No arg
        err = self.ui.execute_command("abort")
        self.assertIn("[ERROR] Usage: abort", err)

        # Deploy and abort
        self.ui.execute_command("scan 10.0.0.1")
        abort_res = self.ui.execute_command("abort 10.0.0.1")
        self.assertIn("aborted and hardware resources reclaimed", abort_res)

    def test_execute_command_exit_and_unknown(self) -> None:
        self.assertEqual(self.ui.execute_command("exit"), "EXIT")
        self.assertEqual(self.ui.execute_command("quit"), "EXIT")

        unknown = self.ui.execute_command("nuke 10.0.0.1")
        self.assertIn("[ERROR] Unknown command: 'nuke'", unknown)

    def test_run_interactive_loop_exit(self) -> None:
        inputs = iter(["status", "exit"])
        outputs: List[str] = []

        def mock_input(prompt: str = "") -> str:
            return next(inputs)

        def mock_print(text: str = "") -> None:
            outputs.append(text)

        self.ui.run_interactive_loop(input_fn=mock_input, output_fn=mock_print)
        joined_output = "\n".join(outputs)
        self.assertIn("Connection severed. Exiting simulator.", joined_output)


if __name__ == "__main__":
    unittest.main()
