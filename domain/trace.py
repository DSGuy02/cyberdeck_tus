from abc import ABC, abstractmethod
from typing import List, Optional

from .deck import CyberDeck
from .node import NetworkNode


class BaseIceDaemon(ABC):
    """Abstract base class representing an Intrusion Countermeasure Electronics (ICE) daemon."""

    def __init__(self, name: str, trigger_threshold: float = 50.0) -> None:
        if not name or not name.strip():
            raise ValueError("ICE daemon name cannot be empty.")
        if not (0.0 <= trigger_threshold <= 100.0):
            raise ValueError("Trigger threshold must be between 0.0 and 100.0 percent.")

        self.name: str = name.strip()
        self.trigger_threshold: float = trigger_threshold
        self.is_active: bool = False

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False

    @abstractmethod
    def execute_countermeasure(self, engine: "TraceEngine") -> None:
        """Executes defensive response when active during a trace tick."""
        pass


class TraceAcceleratorIce(BaseIceDaemon):
    """Defensive ICE that boosts detection rate when system trace surpasses its threshold."""

    def __init__(
        self,
        name: str = "TraceAccelerator",
        trigger_threshold: float = 40.0,
        boost_rate: float = 2.0,
    ) -> None:
        super().__init__(name=name, trigger_threshold=trigger_threshold)
        if boost_rate <= 0:
            raise ValueError("Boost rate must be greater than zero.")
        self.boost_rate: float = boost_rate
        self.applied: bool = False

    def execute_countermeasure(self, engine: "TraceEngine") -> None:
        if not self.applied:
            engine.detection_rate += self.boost_rate
            self.applied = True


class FirewallLockIce(BaseIceDaemon):
    """Targeted ICE that locks a specific vulnerable server when defensive alert triggers."""

    def __init__(
        self,
        target_node: NetworkNode,
        name: str = "FirewallLockdown",
        trigger_threshold: float = 75.0,
    ) -> None:
        super().__init__(name=name, trigger_threshold=trigger_threshold)
        if not isinstance(target_node, NetworkNode):
            raise TypeError("Target node must be an instance of NetworkNode.")
        self.target_node: NetworkNode = target_node
        self.has_triggered: bool = False

    def execute_countermeasure(self, engine: "TraceEngine") -> None:
        if not self.has_triggered:
            self.target_node.lock_node()
            self.has_triggered = True


class TraceEngine:
    """Manages defensive threat tracing, alert states, and reactive countermeasure daemons."""

    def __init__(
        self,
        base_detection_rate: float = 2.0,
        alert_threshold: float = 50.0,
    ) -> None:
        if base_detection_rate <= 0.0:
            raise ValueError("Base detection rate must be greater than zero.")
        if not (1.0 <= alert_threshold < 100.0):
            raise ValueError("Alert threshold must be between 1.0 and 99.0 percent.")

        self.trace_percentage: float = 0.0
        self.base_detection_rate: float = base_detection_rate
        self.detection_rate: float = base_detection_rate
        self.alert_threshold: float = alert_threshold
        self.is_alerted: bool = False
        self.is_game_over: bool = False
        self.active_ice: List[BaseIceDaemon] = []

    def add_ice(self, daemon: BaseIceDaemon) -> None:
        """Registers a countermeasure daemon to the trace monitor."""
        if not isinstance(daemon, BaseIceDaemon):
            raise TypeError("Expected an instance of BaseIceDaemon.")
        if daemon not in self.active_ice:
            self.active_ice.append(daemon)

    def increment_trace(self, amount: float) -> float:
        """Increases trace percentage, clamping at 100.0% and checking alert/game over conditions."""
        if amount < 0.0:
            raise ValueError("Trace increment amount cannot be negative.")

        self.trace_percentage = min(100.0, self.trace_percentage + amount)

        if not self.is_alerted and self.trace_percentage >= self.alert_threshold:
            self.trigger_alarm()

        self.check_game_over()
        return self.trace_percentage

    def dampen_trace(self, amount: float) -> float:
        """Reduces trace percentage, clamping at a minimum of 0.0%."""
        if amount < 0.0:
            raise ValueError("Trace dampening amount cannot be negative.")

        self.trace_percentage = max(0.0, self.trace_percentage - amount)
        return self.trace_percentage

    def trigger_alarm(self) -> None:
        """Escalates defense to an alerted state, increasing the passive detection rate."""
        self.is_alerted = True
        # Alarm state increases detection pressure by 50%
        self.detection_rate = max(self.detection_rate, self.base_detection_rate * 1.5)

    def check_game_over(self) -> bool:
        """Evaluates whether trace saturation has resulted in connection termination."""
        if self.trace_percentage >= 100.0:
            self.is_game_over = True
            return True
        return False

    def tick(self, deck: Optional[CyberDeck] = None) -> None:
        """Advances the defensive clock, evaluating active program noise and ICE triggers."""
        if self.is_game_over:
            return

        # Calculate noise generated by active programs running on the player's deck
        noise_factor = 0.0
        if deck is not None:
            if not isinstance(deck, CyberDeck):
                raise TypeError("Expected an instance of CyberDeck.")
            # Each active program generates trace noise proportional to its RAM consumption
            noise_factor = sum(prog.ram_cost * 0.5 for prog in deck.active_programs)

        # Increment trace by detection rate plus active intrusion noise
        total_increment = self.detection_rate + noise_factor
        self.increment_trace(total_increment)

        # Evaluate and trigger ICE daemons based on current trace level
        for daemon in self.active_ice:
            if self.trace_percentage >= daemon.trigger_threshold:
                if not daemon.is_active:
                    daemon.activate()
                daemon.execute_countermeasure(self)
