from typing import List

from .program import BaseProgram


class CyberDeck:
    """Simulates the player's cyberdeck hardware, managing RAM allocation and program execution."""

    def __init__(self, total_ram: int = 8, cpu_cores: int = 2) -> None:
        if total_ram < 1:
            raise ValueError("Total RAM must be at least 1.")
        if cpu_cores < 1:
            raise ValueError("CPU cores must be at least 1.")

        self.total_ram: int = total_ram
        self.used_ram: int = 0
        self.cpu_cores: int = cpu_cores
        self.active_programs: List[BaseProgram] = []

    @property
    def available_ram(self) -> int:
        """Returns the remaining unallocated RAM."""
        return self.total_ram - self.used_ram

    @property
    def available_cores(self) -> int:
        """Returns the number of available CPU execution cores."""
        return self.cpu_cores - len(self.active_programs)

    def can_run(self, program: BaseProgram) -> bool:
        """Determines if a program can be allocated and scheduled without exceeding hardware limits."""
        if not isinstance(program, BaseProgram):
            return False
        if program in self.active_programs:
            return False
        if program.is_complete or program.is_aborted:
            return False
        if len(self.active_programs) >= self.cpu_cores:
            return False
        if self.available_ram < program.ram_cost:
            return False
        return True

    def allocate_ram(self, amount: int) -> None:
        """Allocates a discrete block of RAM if available."""
        if amount < 1:
            raise ValueError("RAM allocation amount must be at least 1.")
        if self.available_ram < amount:
            raise ValueError(f"Insufficient RAM: requested {amount}MB, available {self.available_ram}MB.")
        self.used_ram += amount

    def release_ram(self, amount: int) -> None:
        """Releases a discrete block of allocated RAM."""
        if amount < 1:
            raise ValueError("RAM release amount must be at least 1.")
        if self.used_ram < amount:
            raise ValueError(f"Cannot release {amount}MB: only {self.used_ram}MB currently allocated.")
        self.used_ram -= amount

    def load_program(self, program: BaseProgram) -> None:
        """Loads and starts a program on the cyberdeck, reserving its required RAM and a CPU thread."""
        if not isinstance(program, BaseProgram):
            raise TypeError("Expected an instance of BaseProgram.")
        if program in self.active_programs:
            raise ValueError(f"Program {program.name} is already running.")
        if program.is_complete or program.is_aborted:
            raise ValueError(f"Cannot load program {program.name}: it is already complete or aborted.")
        if len(self.active_programs) >= self.cpu_cores:
            raise ValueError(f"CPU limit reached: all {self.cpu_cores} cores are occupied.")
        if self.available_ram < program.ram_cost:
            raise ValueError(
                f"Insufficient RAM to load {program.name}: requires {program.ram_cost}MB, available {self.available_ram}MB."
            )

        self.allocate_ram(program.ram_cost)
        self.active_programs.append(program)

    def abort_program(self, program: BaseProgram) -> None:
        """Aborts an active program immediately and reclaims its hardware resources."""
        if program not in self.active_programs:
            raise ValueError(f"Program {program.name} is not currently running on this deck.")

        program.abort()
        self.active_programs.remove(program)
        self.release_ram(program.ram_cost)

    def tick_all(self) -> List[BaseProgram]:
        """Advances each active program by one execution tick and reclaims resources for completed ones."""
        completed_programs: List[BaseProgram] = []

        # Iterate over a shallow copy so completed items can be safely removed
        for program in list(self.active_programs):
            is_finished = program.execute_step()
            if is_finished:
                self.active_programs.remove(program)
                self.release_ram(program.ram_cost)
                completed_programs.append(program)

        return completed_programs
