import unittest

from domain.deck import CyberDeck
from domain.node import NetworkNode, NodeState
from domain.program import PortScanner
from domain.trace import BaseIceDaemon, FirewallLockIce, TraceAcceleratorIce, TraceEngine


class TestTraceEngineAndIce(unittest.TestCase):
    def setUp(self) -> None:
        self.node = NetworkNode(
            ip="10.0.0.99",
            hostname="secure-gateway",
            security_level=2,
            ports={80: False, 443: False},
        )
        self.engine = TraceEngine(base_detection_rate=5.0, alert_threshold=50.0)
        self.deck = CyberDeck(total_ram=8, cpu_cores=2)

    def test_base_ice_is_abstract(self) -> None:
        with self.assertRaises(TypeError):
            BaseIceDaemon(name="GenericIce", trigger_threshold=50.0)  # type: ignore

    def test_ice_daemon_input_validation(self) -> None:
        with self.assertRaises(ValueError):
            TraceAcceleratorIce(name="")

        with self.assertRaises(ValueError):
            TraceAcceleratorIce(trigger_threshold=-5.0)

        with self.assertRaises(ValueError):
            TraceAcceleratorIce(trigger_threshold=105.0)

        with self.assertRaises(ValueError):
            TraceAcceleratorIce(boost_rate=0.0)

        with self.assertRaises(TypeError):
            FirewallLockIce(target_node="not-a-node")  # type: ignore

    def test_trace_engine_initialization_and_validation(self) -> None:
        self.assertEqual(self.engine.trace_percentage, 0.0)
        self.assertEqual(self.engine.base_detection_rate, 5.0)
        self.assertEqual(self.engine.detection_rate, 5.0)
        self.assertEqual(self.engine.alert_threshold, 50.0)
        self.assertFalse(self.engine.is_alerted)
        self.assertFalse(self.engine.is_game_over)
        self.assertEqual(len(self.engine.active_ice), 0)

        with self.assertRaises(ValueError):
            TraceEngine(base_detection_rate=0.0)

        with self.assertRaises(ValueError):
            TraceEngine(alert_threshold=0.0)

        with self.assertRaises(ValueError):
            TraceEngine(alert_threshold=100.0)

    def test_increment_and_dampen_trace_clamping(self) -> None:
        self.engine.increment_trace(25.0)
        self.assertEqual(self.engine.trace_percentage, 25.0)

        self.engine.dampen_trace(10.0)
        self.assertEqual(self.engine.trace_percentage, 15.0)

        # Dampen below zero clamps at 0.0
        self.engine.dampen_trace(50.0)
        self.assertEqual(self.engine.trace_percentage, 0.0)

        # Increment above 100 clamps at 100.0 and triggers game over
        self.engine.increment_trace(120.0)
        self.assertEqual(self.engine.trace_percentage, 100.0)
        self.assertTrue(self.engine.is_game_over)

        with self.assertRaises(ValueError):
            self.engine.increment_trace(-5.0)

        with self.assertRaises(ValueError):
            self.engine.dampen_trace(-5.0)

    def test_alert_threshold_and_alarm_trigger(self) -> None:
        self.assertFalse(self.engine.is_alerted)

        # Incrementing just below threshold should not alert
        self.engine.increment_trace(49.0)
        self.assertFalse(self.engine.is_alerted)

        # Reaching or surpassing threshold triggers alarm
        self.engine.increment_trace(2.0)
        self.assertTrue(self.engine.is_alerted)
        # Alert state escalates detection rate by 1.5x (5.0 * 1.5 = 7.5)
        self.assertEqual(self.engine.detection_rate, 7.5)

    def test_add_ice_daemon(self) -> None:
        ice = TraceAcceleratorIce(trigger_threshold=30.0)
        self.engine.add_ice(ice)
        self.assertEqual(len(self.engine.active_ice), 1)

        # Duplicate addition ignored
        self.engine.add_ice(ice)
        self.assertEqual(len(self.engine.active_ice), 1)

        with self.assertRaises(TypeError):
            self.engine.add_ice("invalid-daemon")  # type: ignore

    def test_tick_advancement_and_program_noise(self) -> None:
        # Tick with no deck advances by base rate (5.0)
        self.engine.tick()
        self.assertEqual(self.engine.trace_percentage, 5.0)

        # Load program on cyberdeck (PortScanner costs 2 RAM -> generates 1.0 noise)
        prog = PortScanner(target_node=self.node, ram_cost=2, execution_time=3)
        self.deck.load_program(prog)

        # Next tick: base rate 5.0 + noise 1.0 = 6.0 increment (total 11.0)
        self.engine.tick(deck=self.deck)
        self.assertEqual(self.engine.trace_percentage, 11.0)

        with self.assertRaises(TypeError):
            self.engine.tick(deck="invalid-deck")  # type: ignore

    def test_trace_accelerator_ice_trigger(self) -> None:
        ice = TraceAcceleratorIce(trigger_threshold=20.0, boost_rate=3.0)
        self.engine.add_ice(ice)

        self.engine.increment_trace(15.0)
        self.assertFalse(ice.is_active)
        self.assertEqual(self.engine.detection_rate, 5.0)

        # Tick pushes trace from 15.0 to 20.0, crossing threshold
        self.engine.tick()
        self.assertTrue(self.engine.trace_percentage >= 20.0)
        self.assertTrue(ice.is_active)
        # Detection rate should now include the boost (5.0 + 3.0 = 8.0)
        self.assertEqual(self.engine.detection_rate, 8.0)

    def test_firewall_lock_ice_trigger(self) -> None:
        self.node.probe_ports()
        self.node.open_port(80)
        self.assertEqual(self.node.state, NodeState.PROBED)
        self.assertTrue(self.node.ports[80])

        ice = FirewallLockIce(target_node=self.node, trigger_threshold=50.0)
        self.engine.add_ice(ice)

        # Trace below threshold
        self.engine.increment_trace(40.0)
        self.assertFalse(ice.is_active)
        self.assertEqual(self.node.state, NodeState.PROBED)

        # Pushing trace to 55.0 triggers lockdown
        self.engine.increment_trace(15.0)
        ice.execute_countermeasure(self.engine)
        self.assertEqual(self.node.state, NodeState.LOCKED)
        self.assertFalse(self.node.ports[80])


if __name__ == "__main__":
    unittest.main()
