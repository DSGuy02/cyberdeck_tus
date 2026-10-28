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

---

## Iteration 2 - Network Graph and Subnet Routing (28/10/2026)

### Activity Descriptions
- Implemented the `NetworkGraph` class in `domain/graph.py` to manage how `NetworkNode` objects are connected together in a network topology.
- Added methods to register nodes, link them with directed or bidirectional edges, look up adjacent nodes, and serialise the graph into a dictionary format.
- Implemented `is_reachable()` using a breadth-first search (BFS) queue to enforce network pivoting rules, where deeper nodes can only be accessed after intermediate parent nodes have been exploited.
- Wrote unit tests in `tests/test_graph.py` to test graph connections, pivoting across three nodes (gateway, proxy, and vault), and node locking behaviour.

### OOP Design Breakdown
- **`NetworkGraph` (Class)**:
  - **Attributes (What it knows)**: `nodes` (dict mapping IP strings to `NetworkNode` objects), `edges` (list of `(source_ip, target_ip)` tuples), and `root_node` (optional string storing the entry gateway IP).
  - **Methods (What it does)**:
    - `add_node(node, is_root)`: Validates and registers a `NetworkNode` in the graph and assigns the root node if needed.
    - `connect(source_ip, target_ip, bidirectional)`: Creates a connection between two existing nodes and prevents self-loops or duplicate edges.
    - `get_adjacent(ip)`: Returns a list of `NetworkNode` instances directly connected to the given IP address.
    - `is_reachable(target_ip)`: Traverses the graph from `root_node` using BFS, only stepping through nodes whose state is `NodeState.EXPLOITED`.
    - `serialize()`: Exports the graph's root node, node states, and edges as a plain Python dictionary.

### Key Accomplishments
- Completed Stage 1 (Core Domain Engine) of the project proposal with both `NetworkNode` and `NetworkGraph` working together.
- Got all 11 unit tests passing across `test_node.py` and `test_graph.py`, confirming that internal subnet nodes stay unreachable until intermediate proxies are breached, and become unreachable again if an intermediate proxy is locked.

### Challenges Faced
- Making sure that cyclic connections (since bidirectional edges create loops between two nodes) did not cause an infinite loop when checking if a target node is reachable. This was resolved by maintaining a `visited` set inside `is_reachable()` alongside a `deque` queue so each node is only checked once per traversal.

### Learning Reflections
- Using `NetworkNode` objects inside `NetworkGraph` showed how object composition works in practice. Instead of the graph manually tracking port numbers or firewall flags, it simply checks `current_node.state == NodeState.EXPLOITED` while handling the routing logic itself.
