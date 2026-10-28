import unittest
from domain.node import NetworkNode, NodeState


class TestNetworkNode(unittest.TestCase):
    def setUp(self) -> None:
        self.node = NetworkNode(
            ip="192.168.1.10",
            hostname="auth-srv-01",
            security_level=2,
            ports={22: False, 443: False},
            data_payload="ROOT_CREDENTIALS_HASH",
        )

    def test_initial_state_and_attributes(self) -> None:
        self.assertEqual(self.node.ip, "192.168.1.10")
        self.assertEqual(self.node.hostname, "auth-srv-01")
        self.assertEqual(self.node.security_level, 2)
        self.assertEqual(self.node.state, NodeState.UNDISCOVERED)
        self.assertEqual(self.node.ports, {22: False, 443: False})
        self.assertEqual(self.node.data_payload, "ROOT_CREDENTIALS_HASH")

    def test_input_validation(self) -> None:
        with self.assertRaises(ValueError):
            NetworkNode(ip="", hostname="valid-host")
        with self.assertRaises(ValueError):
            NetworkNode(ip="10.0.0.1", hostname="   ")
        with self.assertRaises(ValueError):
            NetworkNode(ip="10.0.0.1", hostname="valid-host", security_level=0)

    def test_probe_ports_transitions_state(self) -> None:
        ports = self.node.probe_ports()
        self.assertEqual(self.node.state, NodeState.PROBED)
        self.assertEqual(ports, {22: False, 443: False})

    def test_open_port_requires_probed_state(self) -> None:
        self.assertFalse(self.node.open_port(22))
        self.node.probe_ports()
        self.assertTrue(self.node.open_port(22))
        self.assertTrue(self.node.ports[22])
        self.assertFalse(self.node.open_port(8080))

    def test_breach_firewall_flow(self) -> None:
        self.assertFalse(self.node.breach_firewall())

        self.node.probe_ports()
        self.assertFalse(self.node.breach_firewall())

        self.node.open_port(22)
        self.assertFalse(self.node.breach_firewall())

        self.node.open_port(443)
        self.assertTrue(self.node.breach_firewall())
        self.assertEqual(self.node.state, NodeState.EXPLOITED)

    def test_extract_data_requires_exploited_state(self) -> None:
        with self.assertRaises(PermissionError):
            self.node.extract_data()

        self.node.probe_ports()
        self.node.open_port(22)
        self.node.open_port(443)
        self.node.breach_firewall()

        payload = self.node.extract_data()
        self.assertEqual(payload, "ROOT_CREDENTIALS_HASH")
        self.assertIsNone(self.node.extract_data())

    def test_lock_node_prevents_actions_and_resets_ports(self) -> None:
        self.node.probe_ports()
        self.node.open_port(22)
        self.node.lock_node()

        self.assertEqual(self.node.state, NodeState.LOCKED)
        self.assertEqual(self.node.ports, {22: False, 443: False})
        self.assertFalse(self.node.open_port(22))
        self.assertFalse(self.node.breach_firewall())

        with self.assertRaises(PermissionError):
            self.node.probe_ports()


if __name__ == "__main__":
    unittest.main()
