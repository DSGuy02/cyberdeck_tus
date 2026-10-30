CyberDeck Development Log


28/10/2026 - Iteration 1: Core Node Domain Model

Activity Descriptions

Set up the project folder structure and initialised the Git repository with a .gitignore file to keep Python cache and virtual environment files out of version control.
Started Stage 1 of the project by building the core domain model in domain/node.py to represent target machines on a simulated network.
Implemented the NodeState enum and the NetworkNode class with full state management, input validation, and error handling.
Wrote unit tests in tests/test_node.py using the unittest library to test node setup, input checks, and state changes.

OOP Design and Implementation

In this problem, each server or computer on the target network naturally exists as its own object with its own security state.
NodeState was created as an Enum to hold the four states a machine can be in during a run: UNDISCOVERED, PROBED, EXPLOITED, and LOCKED.
NetworkNode was defined as the main class for a target machine. For its attributes (what the object knows), it stores the ip address, hostname, security_level, current state, a ports dictionary that maps port numbers to a True or False open status, and an optional data_payload string representing files stored on the machine.
In the constructor, input validation was added so that passing an empty IP, an empty hostname, or a security level below 1 raises a ValueError right away.
For its methods (what the object does), probe_ports checks that the node is not locked, updates the state from UNDISCOVERED to PROBED, and returns a copy of the ports dictionary. open_port takes a port number and sets it to True if the node has already been probed. breach_firewall checks that the node is probed and that all ports in the dictionary are open before changing the state to EXPLOITED. extract_data returns the data_payload and clears it to None so it can only be taken once, and raises a PermissionError if the node has not been exploited yet. Finally, lock_node sets the state to LOCKED and resets every port back to False.

Key Accomplishments

Got a working NetworkNode class and NodeState enum implemented with proper input validation and state rules.
Successfully got all 7 unit tests passing in tests/test_node.py, confirming that ports cannot be opened and data cannot be extracted unless the node goes through the proper sequence of states.

Challenges Faced

One challenge that came up was deciding how to handle actions when someone tries to run them out of order, such as trying to extract data before breaching the firewall or probing a node that is already locked. To fix this, state checks were added at the start of each method. Actions like open_port and breach_firewall return False if the prerequisites are not met, while invalid access attempts like probing a locked node or extracting data early raise a PermissionError.

Learning Reflections

Building the node logic around object state and methods made it much easier to keep track of what is allowed on a target machine at any point. Writing unit tests alongside the class also helped catch edge cases early before moving on to connecting multiple nodes together.




28/10/2026 - Iteration 2: Network Graph and Subnet Routing

Activity Descriptions

Implemented the NetworkGraph class in domain/graph.py to connect multiple NetworkNode objects together and represent a full network layout.
Added methods to add nodes to the network, connect them with directed or two-way edges, get neighbouring nodes, and export the graph data as a dictionary.
Implemented the is_reachable method using a breadth-first search queue to handle network pivoting, so deeper nodes on a subnet can only be reached after the nodes in front of them have been exploited.
Created tests/test_graph.py with unit tests covering node registration, edge connections, pivoting across a gateway, proxy, and vault, and locking behaviour.

OOP Design and Implementation

While NetworkNode represents a single machine, NetworkGraph represents the network topology that holds those machines and tracks how they are linked.
For its attributes (what the object knows), NetworkGraph holds a nodes dictionary mapping IP address strings to their NetworkNode objects, an edges list storing pairs of connected source and target IPs, and a root_node string that keeps track of the starting gateway IP.
For its methods (what the object does), add_node checks that the object passed in is a valid NetworkNode and not a duplicate IP before storing it and setting the root node if needed. connect links two node IPs together, blocks nodes from connecting to themselves, and adds edges in both directions by default. get_adjacent returns a list of NetworkNode objects connected to a given IP. is_reachable starts from the root_node and uses a deque queue to search through the graph, only moving past a node if its state is EXPLOITED. serialize converts the whole graph into a dictionary so the network state can be saved or inspected easily.
This setup uses object composition by having NetworkGraph manage a collection of NetworkNode instances and rely on each node's state attribute when checking if the player can pivot deeper into the network.

Key Accomplishments

Completed Stage 1 of the project proposal with both NetworkNode and NetworkGraph working together as a headless domain engine.
Successfully got all 11 unit tests passing across test_node.py and test_graph.py.
Verified that internal nodes stay unreachable until the gateway and proxy nodes in front of them are exploited, and that locking a proxy node cuts off access to deeper nodes again.

Challenges Faced

Because connections between nodes are two-way by default, traversing the graph to check if a target IP is reachable could get stuck bouncing back and forth between two exploited nodes in an infinite loop. The way to mitigate this was to keep a visited set inside the is_reachable method alongside the deque queue, so each node IP is only queued and checked once during a search.

Learning Reflections

Working on NetworkGraph showed how useful it is to separate responsibilities between classes. Because NetworkNode already handles its own ports and firewall state, NetworkGraph did not need to manage any port logic and only needed to check if a node was exploited before stepping through it.




30/10/2026 - Iteration 3: Hardware Resource Manager and Program Hierarchy

Activity Descriptions

Implemented the BaseProgram abstract base class and concrete intrusion programs in domain/program.py.
Created PortScanner, BruteForcer, and DataExtractor subclasses to represent modular intrusion tools that execute over time.
Implemented the CyberDeck class in domain/deck.py to simulate hardware constraints including finite RAM and limited CPU processing cores.
Added resource allocation, process scheduling, program aborting, and a tick execution loop that advances programs and reclaims hardware memory upon completion.
Exported all new domain classes through domain/__init__.py for cleaner package imports.
Wrote unit tests in tests/test_deck.py covering abstract base class enforcement, program lifecycles, memory bounds, CPU core limits, and state changes on target nodes.

OOP Design and Implementation

In this stage, the problem requires modelling both the player's physical hardware rig and the software tools they deploy during an infiltration.
BaseProgram was designed as an abstract base class using Python's abc module so that all tools share a common interface while providing unique behaviour. For its attributes, BaseProgram stores the tool name, ram_cost, execution_time in discrete ticks, the target NetworkNode object, current_step, progress percentage from 0 to 100, is_complete, and is_aborted. For its methods, execute_step increments progress and calls the abstract on_complete method once progress reaches 100, while abort stops execution immediately.
Three polymorphic subclasses inherit from BaseProgram. PortScanner probes the target node to reveal ports. BruteForcer targets a specific port number, cracks it open, and checks whether all ports are open to breach the firewall. DataExtractor checks that the target node is exploited and exfiltrates its confidential payload, raising a PermissionError if the node has not yet been breached.
CyberDeck was created to represent the hardware resource manager. For its attributes, it tracks total_ram, used_ram, cpu_cores, and a list of active_programs. It exposes available_ram and available_cores properties. For its methods, can_run verifies that there is enough free memory and an idle CPU thread before starting a tool. load_program reserves the required RAM and adds the tool to active_programs. abort_program stops a running process and reclaims its RAM immediately. tick_all steps every running program forward by one tick, checks for completed programs, triggers their on_complete hooks, and automatically reclaims their allocated RAM.
This design uses polymorphism so CyberDeck can manage and tick any subclass of BaseProgram without needing to know the specific tool details. It also uses object composition because CyberDeck holds active BaseProgram objects, and each BaseProgram holds a reference to a target NetworkNode.

Key Accomplishments

Implemented a working CyberDeck hardware scheduler and a polymorphic BaseProgram tool hierarchy.
Completed Stage 2 of the project proposal covering hardware resource limits and program lifecycles.
Successfully got all 22 unit tests passing across test_node.py, test_graph.py, and test_deck.py.
Verified that programs cleanly take up RAM and CPU cores while running and release their resources automatically back to the cyberdeck once finished.

Challenges Faced

One challenge that came up was modifying the list of active programs inside the tick_all method. When a program completes during a tick, removing it directly from the active_programs list while looping through it in Python causes items to be skipped or raises iteration errors. The way to mitigate this was to loop over a shallow copy of the active_programs list. This allowed completed programs to be safely removed from the original list and their RAM freed without interfering with the loop.

Learning Reflections

Using an abstract base class made building new intrusion tools straightforward because each subclass only needed to implement on_complete and specify its resource costs. Managing finite hardware constraints also showed how OOP state can naturally prevent invalid actions in a simulation, such as stopping a player from running more programs than their cyberdeck has memory or CPU threads to support.
