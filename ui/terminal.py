import shlex
from typing import Callable, List

from domain.node import NodeState
from domain.session import GameSession


class TerminalUI:
    """Renders the decoupled terminal user interface and handles player commands."""

    def __init__(self, session: GameSession, use_colors: bool = True) -> None:
        if not isinstance(session, GameSession):
            raise TypeError("Expected an instance of GameSession.")
        self.session: GameSession = session
        self.use_colors: bool = use_colors

    def _color(self, text: str, code: str) -> str:
        if not self.use_colors:
            return text
        return f"\033[{code}m{text}\033[0m"

    def green(self, text: str) -> str:
        return self._color(text, "92")

    def red(self, text: str) -> str:
        return self._color(text, "91")

    def yellow(self, text: str) -> str:
        return self._color(text, "93")

    def cyan(self, text: str) -> str:
        return self._color(text, "96")

    def bold(self, text: str) -> str:
        return self._color(text, "1")

    def dim(self, text: str) -> str:
        return self._color(text, "90")

    def render_bar(self, current: float, total: float, width: int = 16, fill_char: str = "█", empty_char: str = "░") -> str:
        """Renders an ASCII progress / capacity meter."""
        if total <= 0:
            return empty_char * width
        ratio = max(0.0, min(1.0, current / total))
        filled = int(round(ratio * width))
        return (fill_char * filled) + (empty_char * (width - filled))

    def render_banner(self) -> str:
        line1 = "╔" + "═" * 74 + "╗"
        title = "CYBERDECK v1.0 // TERMINAL INFILTRATION HUD"
        line2 = f"║{title:^74}║"
        line3 = "╚" + "═" * 74 + "╝"
        return f"{self.cyan(line1)}\n{self.bold(line2)}\n{self.cyan(line3)}"

    def render_telemetry(self) -> str:
        turn_str = f"Turn: {self.session.turn:02d}"

        # RAM telemetry
        total_ram = self.session.deck.total_ram
        used_ram = self.session.deck.used_ram
        ram_bar = self.render_bar(used_ram, total_ram, width=12)
        ram_display = f"RAM: [{self.cyan(ram_bar)}] {used_ram}/{total_ram} MB (Avail: {self.session.deck.available_ram} MB)"

        # CPU telemetry
        total_cpu = self.session.deck.cpu_cores
        used_cpu = len(self.session.deck.active_programs)
        cpu_bar = self.render_bar(used_cpu, total_cpu, width=6)
        cpu_display = f"CPU: [{self.cyan(cpu_bar)}] {used_cpu}/{total_cpu} Cores"

        # Trace telemetry
        trace_pct = self.session.trace.trace_percentage
        alert_status = "ELEVATED" if self.session.trace.is_alerted else "NORMAL"
        trace_bar = self.render_bar(trace_pct, 100.0, width=14)

        if trace_pct >= 75.0:
            trace_colored = self.red(f"[{trace_bar}] {trace_pct:5.1f}% [ALERT: {alert_status}]")
        elif self.session.trace.is_alerted:
            trace_colored = self.yellow(f"[{trace_bar}] {trace_pct:5.1f}% [ALERT: {alert_status}]")
        else:
            trace_colored = self.green(f"[{trace_bar}] {trace_pct:5.1f}% [ALERT: {alert_status}]")

        telemetry_lines = [
            f"┌─ TELEMETRY ── ({turn_str}) " + "─" * 48 + "┐",
            f"│  {ram_display:<45} {cpu_display:<26}│",
            f"│  DEFENSE TRACE: {trace_colored:<65}│",
            "└" + "─" * 74 + "┘",
        ]
        return "\n".join(telemetry_lines)

    def render_network_topology(self) -> str:
        header = f"┌─ NETWORK TOPOLOGY " + "─" * 55 + "┐"
        cols = f"│ {'IP ADDRESS':<15} {'HOSTNAME':<16} {'SEC':<5} {'REACHABLE':<11} {'STATUS':<12} {'PORTS':<8}│"
        sep = "├" + "─" * 74 + "┤"

        rows: List[str] = [header, cols, sep]

        for ip, node in self.session.graph.nodes.items():
            is_reach = "YES" if self.session.graph.is_reachable(ip) else "NO"

            # Badge formatting
            if node.state == NodeState.EXPLOITED:
                badge = self.green("EXPLOITED")
            elif node.state == NodeState.PROBED:
                badge = self.yellow("PROBED")
            elif node.state == NodeState.LOCKED:
                badge = self.red("LOCKED")
            else:
                badge = self.dim("UNDISCOVERED")

            # Ports summary
            if not node.ports:
                ports_str = "None"
            elif node.state == NodeState.UNDISCOVERED:
                ports_str = f"? ({len(node.ports)})"
            else:
                open_cnt = sum(1 for st in node.ports.values() if st)
                ports_str = f"{open_cnt}/{len(node.ports)} Open"

            # Format row with plain widths then replace badge
            row_str = f"│ {node.ip:<15} {node.hostname:<16} Lvl {node.security_level:<1} {is_reach:<11} {badge:<21} {ports_str:<8}│"
            rows.append(row_str)

        rows.append("└" + "─" * 74 + "┘")
        return "\n".join(rows)

    def render_active_programs(self) -> str:
        header = "┌─ ACTIVE CYBERDECK INTRUSION PROGRAMS " + "─" * 36 + "┐"
        rows: List[str] = [header]

        if not self.session.deck.active_programs:
            rows.append(f"│  {self.dim('(No intrusion programs currently executing)') :<82}│")
        else:
            for prog in self.session.deck.active_programs:
                bar = self.render_bar(prog.progress, 100.0, width=12)
                pct_str = f"{prog.progress:5.1f}%"
                target_str = f"-> {prog.target_node.hostname} ({prog.target_node.ip})"
                prog_line = f"{prog.name:<13} [{self.cyan(bar)}] {pct_str} (RAM: {prog.ram_cost}MB) {target_str}"
                rows.append(f"│  {prog_line:<82}│")

        rows.append("└" + "─" * 74 + "┘")
        return "\n".join(rows)

    def render_event_log(self, limit: int = 5) -> str:
        header = "┌─ INFILTRATION EVENT LOG " + "─" * 49 + "┐"
        rows: List[str] = [header]

        recent_events = self.session.event_log[-limit:]
        if not recent_events:
            rows.append(f"│  {self.dim('(Log empty)') :<82}│")
        else:
            for event in recent_events:
                # Trim to fit box cleanly
                clean_event = event[:70]
                rows.append(f"│  {clean_event:<72}│")

        rows.append("└" + "─" * 74 + "┘")
        return "\n".join(rows)

    def render_dashboard(self) -> str:
        """Assembles the complete infiltration dashboard view."""
        parts = [
            self.render_banner(),
            self.render_telemetry(),
            self.render_network_topology(),
            self.render_active_programs(),
            self.render_event_log(limit=5),
        ]
        return "\n".join(parts)

    def execute_command(self, raw_command: str) -> str:
        """Parses and executes user commands from the terminal prompt."""
        line = raw_command.strip()
        if not line:
            return ""

        try:
            tokens = shlex.split(line)
        except ValueError as err:
            return f"[ERROR] Malformed command input: {err}"

        cmd = tokens[0].lower()
        args = tokens[1:]

        try:
            if cmd == "help":
                return (
                    "Available Commands:\n"
                    "  scan <ip>          Deploy PortScanner to probe ports on reachable node\n"
                    "  crack <ip> <port>  Deploy BruteForcer to open a specific port\n"
                    "  extract <ip>       Deploy DataExtractor to steal data from exploited node\n"
                    "  abort <name/ip>    Abort an active intrusion program and reclaim RAM\n"
                    "  tick [turns]       Advance simulation by N turns (default: 1)\n"
                    "  status             Refresh the telemetry and dashboard\n"
                    "  help               Display this command list\n"
                    "  exit / quit        End infiltration session"
                )

            elif cmd == "status":
                return "Telemetry refreshed."

            elif cmd == "tick":
                turns = 1
                if args:
                    turns = int(args[0])
                    if turns < 1:
                        return "[ERROR] Tick count must be at least 1."
                for _ in range(turns):
                    if self.session.is_finished:
                        break
                    self.session.tick()
                return f"Advanced simulation by {turns} turn(s)."

            elif cmd == "scan":
                if not args:
                    return "[ERROR] Usage: scan <ip>"
                self.session.deploy_scanner(args[0])
                return f"PortScanner successfully queued for {args[0]}."

            elif cmd == "crack":
                if len(args) < 2:
                    return "[ERROR] Usage: crack <ip> <port>"
                port = int(args[1])
                self.session.deploy_brute_forcer(args[0], port)
                return f"BruteForcer queued against port {port} on {args[0]}."

            elif cmd == "extract":
                if not args:
                    return "[ERROR] Usage: extract <ip>"
                self.session.deploy_extractor(args[0])
                return f"DataExtractor queued for {args[0]}."

            elif cmd == "abort":
                if not args:
                    return "[ERROR] Usage: abort <program_name_or_ip>"
                success = self.session.abort_program_by_name(args[0])
                if success:
                    return f"Program '{args[0]}' aborted and hardware resources reclaimed."
                return f"[ERROR] No active program found matching '{args[0]}'."

            elif cmd in ("exit", "quit"):
                return "EXIT"

            else:
                return f"[ERROR] Unknown command: '{cmd}'. Type 'help' for command reference."

        except (ValueError, KeyError, PermissionError, RuntimeError, TypeError) as err:
            return f"[ERROR] {err}"

    def run_interactive_loop(
        self,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
    ) -> None:
        """Runs the interactive Read-Eval-Print Loop (REPL)."""
        output_fn(self.render_dashboard())
        output_fn("\nType 'help' for available commands, or 'exit' to quit.\n")

        while not self.session.is_finished:
            try:
                user_input = input_fn("\ncyberdeck> ")
            except (EOFError, KeyboardInterrupt):
                output_fn("\nSession aborted by user.")
                break

            result = self.execute_command(user_input)
            if result == "EXIT":
                output_fn("Connection severed. Exiting simulator.")
                break

            output_fn(self.render_dashboard())
            if result:
                output_fn(f"\n{result}")

        # Post-game resolution screen
        if self.session.is_victory:
            output_fn(self.green("\n" + "═" * 74))
            output_fn(self.green("MISSION SUCCESS // TARGET OBJECTIVE ACQUIRED // SYSTEM COMPROMISED"))
            output_fn(self.green("═" * 74))
        elif self.session.is_game_over:
            output_fn(self.red("\n" + "═" * 74))
            output_fn(self.red("MISSION FAILURE // DEFENSIVE TRACE SATURATED // CONNECTION PURGED"))
            output_fn(self.red("═" * 74))
