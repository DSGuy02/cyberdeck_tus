import unittest
from domain.graph import NetworkGraph
from domain.node import NetworkNode, NodeState


class TestNetworkGraph(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = NetworkGraph()
        self.gateway = NetworkNode(
            ip="10.0.0.1",
            hostname="gateway-01",
            security_level=1,
            ports={80: False},
        )
        self.proxy = NetworkNode(
            ip="10.0.0.2",
            hostname="proxy-01",
            security_level=2,
            ports={22: False, 443: False},
        )
        self.vault = NetworkNode(
            ip="10.0.0.3",
            hostname="vault-db",
            security_level=3,
            ports={3306: False},
            data_payload="CONFIDENTIAL_RECORDS",
        )

        self.graph.add_node(self.gateway, is_root=True)
        self.graph.add_node(self.proxy)
        self.graph.add_node(self.vault)

        self.graph.connect("10.0.0.1", "10.0.0.2")
        self.graph.connect("10.0.0.2", "10.0.0.3")

    def test_add_node_and_root_assignment(self) -> None:
        self.assertEqual(self.graph.root_node, "10.0.0.1")
        self.assertEqual(len(self.graph.nodes), 3)

        with self.assertRaises(ValueError):
            self.graph.add_node(self.gateway)

        with self.assertRaises(TypeError):
            self.graph.add_node("not-a-node")  # type: ignore

    def test_connect_and_get_adjacent(self) -> None:
        adj_gateway = self.graph.get_adjacent("10.0.0.1")
        self.assertEqual(adj_gateway, [self.proxy])

        adj_proxy = self.graph.get_adjacent("10.0.0.2")
        self.assertEqual(adj_proxy, [self.gateway, self.vault])

        with self.assertRaises(KeyError):
            self.graph.connect("10.0.0.1", "99.99.99.99")

        with self.assertRaises(ValueError):
            self.graph.connect("10.0.0.1", "10.0.0.1")

    def test_reachability_and_pivoting(self) -> None:
        self.assertTrue(self.graph.is_reachable("10.0.0.1"))
        self.assertFalse(self.graph.is_reachable("10.0.0.2"))
        self.assertFalse(self.graph.is_reachable("10.0.0.3"))

        self.gateway.probe_ports()
        self.gateway.open_port(80)
        self.gateway.breach_firewall()

        self.assertTrue(self.graph.is_reachable("10.0.0.2"))
        self.assertFalse(self.graph.is_reachable("10.0.0.3"))

        self.proxy.probe_ports()
        self.proxy.open_port(22)
        self.proxy.open_port(443)
        self.proxy.breach_firewall()

        self.assertTrue(self.graph.is_reachable("10.0.0.3"))

        self.proxy.lock_node()
        self.assertFalse(self.graph.is_reachable("10.0.0.3"))

    def test_serialize_structure(self) -> None:
        data = self.graph.serialize()
        self.assertEqual(data["root_node"], "10.0.0.1")
        self.assertIn("10.0.0.3", data["nodes"])
        self.assertEqual(data["nodes"]["10.0.0.3"]["state"], NodeState.UNDISCOVERED.value)
        self.assertIn(("10.0.0.1", "10.0.0.2"), data["edges"])


if __name__ == "__main__":
    unittest.main()
