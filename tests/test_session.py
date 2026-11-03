import unittest

from domain.deck import CyberDeck
from domain.graph import NetworkGraph
from domain.node import NetworkNode, NodeState
from domain.session import GameSession
from domain.trace import TraceEngine


class TestGameSession(unittest.TestCase):
    def setUp(self) -> None:
        self.gateway = NetworkNode(ip="10.0.0.1", hostname="gw", security_level=1, ports={80: False})
        self.vault = NetworkNode(
            ip="10.0.0.2",
            hostname="vault",
            security_level=2,
            ports={22: False},
            data_payload="SECRET_INTEL",
        )

        self.graph = NetworkGraph()
        self.graph.add_node(self.gateway, is_root=True)
        self.graph.add_node(self.vault)
        self.graph.connect("10.0.0.1", "10.0.0.2")

        self.deck = CyberDeck(total_ram=8, cpu_cores=2)
        self.trace = TraceEngine(base_detection_rate=5.0, alert_threshold=50.0)

        self.session = GameSession(
            graph=self.graph,
            deck=self.deck,
            trace=self.trace,
            target_objective_ip="10.0.0.2",
        )

    def test_initial_state_and_validation(self) -> None:
        self.assertEqual(self.session.turn, 0)
        self.assertFalse(self.session.is_victory)
        self.assertFalse(self.session.is_game_over)
        self.assertFalse(self.session.is_finished)
        self.assertEqual(len(self.session.event_log), 1)

        with self.assertRaises(TypeError):
            GameSession("not-a-graph", self.deck, self.trace)  # type: ignore
        with self.assertRaises(TypeError):
            GameSession(self.graph, "not-a-deck", self.trace)  # type: ignore
        with self.assertRaises(TypeError):
            GameSession(self.graph, self.deck, "not-trace")  # type: ignore

    def test_deploy_scanner_reachability(self) -> None:
        # Gateway is root so it is reachable
        scanner = self.session.deploy_scanner("10.0.0.1")
        self.assertEqual(scanner.target_node.ip, "10.0.0.1")
        self.assertIn(scanner, self.deck.active_programs)

        # Vault is unreachable before gateway is exploited
        with self.assertRaises(PermissionError):
            self.session.deploy_scanner("10.0.0.2")

        with self.assertRaises(KeyError):
            self.session.deploy_scanner("99.99.99.99")

    def test_deploy_brute_forcer_prerequisites(self) -> None:
        # Gateway is undiscovered; cracking should fail until probed
        with self.assertRaises(PermissionError):
            self.session.deploy_brute_forcer("10.0.0.1", 80)

        # Probe gateway
        self.gateway.probe_ports()
        cracker = self.session.deploy_brute_forcer("10.0.0.1", 80)
        self.assertIn(cracker, self.deck.active_programs)

    def test_deploy_extractor_prerequisites(self) -> None:
        self.gateway.probe_ports()
        # Not exploited yet
        with self.assertRaises(PermissionError):
            self.session.deploy_extractor("10.0.0.1")

    def test_abort_program_by_name(self) -> None:
        self.session.deploy_scanner("10.0.0.1")
        self.assertEqual(len(self.deck.active_programs), 1)

        # Abort by IP
        success = self.session.abort_program_by_name("10.0.0.1")
        self.assertTrue(success)
        self.assertEqual(len(self.deck.active_programs), 0)

        # Non-existent
        self.assertFalse(self.session.abort_program_by_name("not-found"))

    def test_tick_turn_and_victory_resolution(self) -> None:
        # Deploy scanner on gateway (takes 2 ticks)
        self.session.deploy_scanner("10.0.0.1")
        self.assertEqual(self.session.turn, 0)

        # Tick 1
        self.session.tick()
        self.assertEqual(self.session.turn, 1)
        self.assertEqual(self.gateway.state, NodeState.UNDISCOVERED)

        # Tick 2: Scanner finishes and probes gateway
        self.session.tick()
        self.assertEqual(self.session.turn, 2)
        self.assertEqual(self.gateway.state, NodeState.PROBED)

        # Deploy cracker on port 80 (takes 2 ticks: security_level 1 * 2)
        self.session.deploy_brute_forcer("10.0.0.1", 80)
        self.session.tick()
        self.session.tick()
        self.assertEqual(self.gateway.state, NodeState.EXPLOITED)

        # Now vault is reachable! Probe vault
        self.assertTrue(self.graph.is_reachable("10.0.0.2"))
        self.session.deploy_scanner("10.0.0.2")
        self.session.tick()
        self.session.tick()
        self.assertEqual(self.vault.state, NodeState.PROBED)

        # Crack vault port 22 (security_level 2 * 2 = 4 ticks)
        self.session.deploy_brute_forcer("10.0.0.2", 22)
        for _ in range(4):
            self.session.tick()
        self.assertEqual(self.vault.state, NodeState.EXPLOITED)

        # Deploy extractor on vault (3 ticks)
        self.session.deploy_extractor("10.0.0.2")
        for _ in range(3):
            self.session.tick()

        # Target objective extracted -> VICTORY!
        self.assertIn("SECRET_INTEL", self.session.exfiltrated_data)
        self.assertTrue(self.session.is_victory)
        self.assertTrue(self.session.is_finished)

    def test_defeat_when_trace_saturates(self) -> None:
        # Force trace to 100%
        self.trace.increment_trace(100.0)
        self.assertTrue(self.session.is_game_over)
        self.assertTrue(self.session.is_finished)

        # Trying to deploy programs after finish raises RuntimeError
        with self.assertRaises(RuntimeError):
            self.session.deploy_scanner("10.0.0.1")


if __name__ == "__main__":
    unittest.main()
