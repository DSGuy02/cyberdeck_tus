# CyberDeck Development Log

## Iteration 1 - Core Node Domain Model (28/10/2026)

### Activity Descriptions
- Set up the project folder structure and initialised the Git repository with a `.gitignore` file to keep cache and environment files out of version control.
- Defined the `NodeState` enum to track the current status of a target machine on the network (`UNDISCOVERED`, `PROBED`, `EXPLOITED`, and `LOCKED`).
- Implemented the `NetworkNode` class in `domain/node.py`. The class was defined as an object featuring properties to store the IP address, hostname, security level, current state, ports dictionary, and data payload.
- Added methods to handle how the node behaves during an infiltration attempt, including `probe_ports()`, `open_port()`, `breach_firewall()`, `extract_data()`, and `lock_node()`.
- Wrote unit tests in `tests/test_node.py` using Python's `unittest` framework to test input validation and state transitions.

### Key Accomplishments
- Implemented a working `NetworkNode` class with proper state checks and input validation.
- Got all 7 unit tests passing to verify that nodes cannot be breached or have data extracted before the required ports are opened and the firewall is bypassed.

### Challenges Faced
- Deciding how strict the state transitions should be when interacting with a node. For example, attempting to open a port on an undiscovered node or extracting data before the firewall is breached needed to be blocked properly. This was addressed by adding state checks at the start of each method and raising a `PermissionError` when an action is attempted out of order or on a locked node.

### Learning Reflections
- Gained better practice structuring a class around object state and behaviour rather than just storing data. Writing the unit tests alongside the class made it much easier to verify that the validation logic worked as intended without needing a user interface yet.
