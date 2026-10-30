import unittest

from domain.deck import CyberDeck
from domain.node import NetworkNode, NodeState
from domain.program import BaseProgram, BruteForcer, DataExtractor, PortScanner


class TestProgramsAndCyberDeck(unittest.TestCase):
    def setUp(self) -> None:
        self.node = NetworkNode(
            ip="192.168.1.50",
            hostname="corp-db-01",
            security_level=2,
            ports={22: False, 80: False},
            data_payload="PATENT_CONFIDENTIAL_BLUEPRINT",
        )
        self.deck = CyberDeck(total_ram=8, cpu_cores=2)

    def test_base_program_is_abstract(self) -> None:
        with self.assertRaises(TypeError):
            BaseProgram("GenericTool", 2, 2, self.node)  # type: ignore

    def test_program_input_validation(self) -> None:
        with self.assertRaises(ValueError):
            PortScanner(target_node=self.node, ram_cost=0)

        with self.assertRaises(ValueError):
            PortScanner(target_node=self.node, execution_time=0)

        with self.assertRaises(TypeError):
            PortScanner(target_node="not-a-node")  # type: ignore

        with self.assertRaises(TypeError):
            BruteForcer(target_node=self.node, target_port="22")  # type: ignore

        with self.assertRaises(ValueError):
            BruteForcer(target_node=self.node, target_port=9999)

    def test_port_scanner_lifecycle(self) -> None:
        scanner = PortScanner(target_node=self.node, ram_cost=2, execution_time=2)
        self.assertEqual(scanner.progress, 0.0)
        self.assertFalse(scanner.is_complete)
        self.assertEqual(self.node.state, NodeState.UNDISCOVERED)

        # First tick: 50%
        finished = scanner.execute_step()
        self.assertFalse(finished)
        self.assertEqual(scanner.progress, 50.0)
        self.assertFalse(scanner.is_complete)

        # Second tick: 100% and triggers probe_ports
        finished = scanner.execute_step()
        self.assertTrue(finished)
        self.assertEqual(scanner.progress, 100.0)
        self.assertTrue(scanner.is_complete)
        self.assertEqual(self.node.state, NodeState.PROBED)
        self.assertEqual(scanner.discovered_ports, {22: False, 80: False})

    def test_brute_forcer_and_firewall_breach(self) -> None:
        # Probe node first
        self.node.probe_ports()

        cracker1 = BruteForcer(target_node=self.node, target_port=22, execution_time=1)
        cracker2 = BruteForcer(target_node=self.node, target_port=80, execution_time=1)

        # Crack first port
        cracker1.execute_step()
        self.assertTrue(self.node.ports[22])
        self.assertEqual(self.node.state, NodeState.PROBED)

        # Crack second port; since all ports are now open, firewall should breach
        cracker2.execute_step()
        self.assertTrue(self.node.ports[80])
        self.assertEqual(self.node.state, NodeState.EXPLOITED)

    def test_data_extractor_lifecycle(self) -> None:
        extractor = DataExtractor(target_node=self.node, execution_time=1)

        # Node is not yet exploited; completion should raise PermissionError
        with self.assertRaises(PermissionError):
            extractor.execute_step()

        # Exploit the node manually
        self.node.probe_ports()
        self.node.open_port(22)
        self.node.open_port(80)
        self.node.breach_firewall()
        self.assertEqual(self.node.state, NodeState.EXPLOITED)

        # New extractor on exploited node
        extractor_valid = DataExtractor(target_node=self.node, execution_time=1)
        extractor_valid.execute_step()
        self.assertEqual(extractor_valid.extracted_payload, "PATENT_CONFIDENTIAL_BLUEPRINT")
        self.assertIsNone(self.node.data_payload)

    def test_program_abort(self) -> None:
        scanner = PortScanner(target_node=self.node, execution_time=3)
        scanner.execute_step()
        self.assertFalse(scanner.is_aborted)

        scanner.abort()
        self.assertTrue(scanner.is_aborted)

        with self.assertRaises(RuntimeError):
            scanner.execute_step()

    def test_cyberdeck_initial_state_and_validation(self) -> None:
        self.assertEqual(self.deck.total_ram, 8)
        self.assertEqual(self.deck.used_ram, 0)
        self.assertEqual(self.deck.available_ram, 8)
        self.assertEqual(self.deck.cpu_cores, 2)
        self.assertEqual(self.deck.available_cores, 2)
        self.assertEqual(len(self.deck.active_programs), 0)

        with self.assertRaises(ValueError):
            CyberDeck(total_ram=0)
        with self.assertRaises(ValueError):
            CyberDeck(cpu_cores=0)

    def test_cyberdeck_ram_allocation_bounds(self) -> None:
        self.deck.allocate_ram(4)
        self.assertEqual(self.deck.used_ram, 4)
        self.assertEqual(self.deck.available_ram, 4)

        with self.assertRaises(ValueError):
            self.deck.allocate_ram(5)  # Exceeds available RAM

        self.deck.release_ram(2)
        self.assertEqual(self.deck.used_ram, 2)

        with self.assertRaises(ValueError):
            self.deck.release_ram(10)  # Releasing more than allocated

    def test_cyberdeck_load_program_and_limits(self) -> None:
        prog1 = PortScanner(target_node=self.node, ram_cost=4, execution_time=2)
        prog2 = PortScanner(target_node=self.node, ram_cost=4, execution_time=2)
        prog3 = PortScanner(target_node=self.node, ram_cost=2, execution_time=2)

        self.assertTrue(self.deck.can_run(prog1))
        self.deck.load_program(prog1)
        self.assertEqual(self.deck.used_ram, 4)
        self.assertEqual(self.deck.available_cores, 1)

        # Duplicate loading blocked
        with self.assertRaises(ValueError):
            self.deck.load_program(prog1)

        # Load second program filling both RAM and CPU cores
        self.assertTrue(self.deck.can_run(prog2))
        self.deck.load_program(prog2)
        self.assertEqual(self.deck.used_ram, 8)
        self.assertEqual(self.deck.available_cores, 0)

        # Attempting to load a third program fails due to CPU limit and RAM limit
        self.assertFalse(self.deck.can_run(prog3))
        with self.assertRaises(ValueError):
            self.deck.load_program(prog3)

        with self.assertRaises(TypeError):
            self.deck.load_program("not-a-program")  # type: ignore

    def test_cyberdeck_abort_program(self) -> None:
        prog = PortScanner(target_node=self.node, ram_cost=3, execution_time=4)
        self.deck.load_program(prog)
        self.assertEqual(self.deck.used_ram, 3)

        self.deck.abort_program(prog)
        self.assertTrue(prog.is_aborted)
        self.assertEqual(self.deck.used_ram, 0)
        self.assertEqual(len(self.deck.active_programs), 0)

        with self.assertRaises(ValueError):
            self.deck.abort_program(prog)  # Not currently running

    def test_cyberdeck_tick_all_lifecycle(self) -> None:
        scanner = PortScanner(target_node=self.node, ram_cost=2, execution_time=2)
        cracker = BruteForcer(target_node=self.node, target_port=22, ram_cost=3, execution_time=1)

        self.deck.load_program(scanner)
        self.deck.load_program(cracker)
        self.assertEqual(self.deck.used_ram, 5)
        self.assertEqual(len(self.deck.active_programs), 2)

        # First tick: cracker takes 1 tick and finishes; scanner takes 2 ticks and stays running
        completed = self.deck.tick_all()
        self.assertEqual(completed, [cracker])
        self.assertEqual(len(self.deck.active_programs), 1)
        self.assertEqual(self.deck.used_ram, 2)  # Cracker's 3MB freed automatically
        self.assertEqual(self.deck.available_cores, 1)
        self.assertEqual(scanner.progress, 50.0)

        # Second tick: scanner finishes, probes node, and frees its 2MB
        completed_second = self.deck.tick_all()
        self.assertEqual(completed_second, [scanner])
        self.assertEqual(len(self.deck.active_programs), 0)
        self.assertEqual(self.deck.used_ram, 0)
        self.assertEqual(self.deck.available_ram, 8)
        self.assertEqual(self.node.state, NodeState.PROBED)


if __name__ == "__main__":
    unittest.main()
