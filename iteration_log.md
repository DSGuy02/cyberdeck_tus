# CyberDeck Development Log

## Iteration 1 - Core Node Domain Model (28/10/2026)

### Activity Descriptions
- Set up the project folder structure and initialised the Git repository with a `.gitignore` file to keep cache and environment files out of version control.
- Implemented the `NodeState` enum and `NetworkNode` class in `domain/node.py` to represent individual target machines on a simulated network.
- Added input validation and error handling (`ValueError` and `PermissionError`) to prevent invalid node creation or out-of-order actions.
- Wrote unit tests in `tests/test_node.py` using Python's `unittest` framework to verify state transitions and validation rules.

### OOP Design Breakdown
- **`NodeState` (Enum)**: Represents the discrete states a target node can be in (`UNDISCOVERED`, `PROBED`, `EXPLOITED`, `LOCKED`).
- **`NetworkNode` (Class)**:
  - **Attributes (What it knows)**: `ip` (str), `hostname` (str), `security_level` (int), `state` (`NodeState`), `ports` (dict mapping port numbers to open/closed status), and `data_payload` (optional string holding target data).
  - **Methods (What it does)**:
    - `probe_ports()`: Reveals the node's ports and moves the state from `UNDISCOVERED` to `PROBED`.
    - `open_port(port)`: Opens a specific port on the node if the node has already been probed.
    - `breach_firewall()`: Checks that all required ports are open and sets the node state to `EXPLOITED`.
    - `extract_data()`: Retrieves and clears the `data_payload` once the node is `EXPLOITED`.
    - `lock_node()`: Locks the node and closes all ports to block any further intrusion attempts.

### Key Accomplishments
- Implemented a working `NetworkNode` class with proper state checks and input validation.
- Got all 7 unit tests passing in `tests/test_node.py`, confirming that nodes cannot be breached or have data extracted before the required ports are opened and the firewall is bypassed.

### Challenges Faced
- Deciding how strict the state transitions should be when interacting with a node. Attempting to open a port on an undiscovered node or extracting data before the firewall is breached needed to be blocked properly. This was addressed by checking the current `NodeState` at the start of each method and raising a `PermissionError` when an action is attempted out of order or on a locked node.

### Learning Reflections
- Structuring `NetworkNode` around clear object state and behaviour made the rules of the simulation easy to follow. Writing unit tests alongside the class made it straightforward to check edge cases and validation logic before building the rest of the network graph.
