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




31/10/2026 - Iteration 4: Defensive Countermeasures and Trace Engine

Activity Descriptions

Implemented the BaseIceDaemon abstract base class and concrete countermeasure daemons in domain/trace.py.
Created TraceAcceleratorIce to escalate system detection speed and FirewallLockIce to automatically lock compromised servers when defensive alerts trigger.
Implemented the TraceEngine class in domain/trace.py to monitor network noise, track intrusion trace percentages, manage alert states, and check session failure conditions.
Integrated defensive surveillance cycles with the CyberDeck hardware model so running active programs generates network noise that advances the trace meter.
Exported the new defensive countermeasure classes in domain/__init__.py.
Wrote unit tests in tests/test_trace.py covering trace increments, trace dampening bounds, alert escalations, ICE activation thresholds, and game over detection.

OOP Design and Implementation

This stage of the project focuses on the defensive antagonist: the systems that detect and push back against unauthorised intrusion.
BaseIceDaemon was created as an abstract base class to define how defensive Intrusion Countermeasure Electronics operate. For its attributes, it stores the daemon name, a trigger_threshold percentage from 0 to 100, and an is_active boolean flag. For its methods, activate and deactivate toggle the daemon state, while execute_countermeasure is defined as an abstract method for specific defensive actions.
Two polymorphic subclasses inherit from BaseIceDaemon. TraceAcceleratorIce activates once trace crosses its threshold and permanently increases the engine detection rate. FirewallLockIce holds a reference to a target NetworkNode and calls its lock_node method when defensive alerts reach high thresholds, resetting its open ports and preventing further data exfiltration.
TraceEngine was implemented to control threat monitoring and game state resolution. For its attributes, it tracks trace_percentage, base_detection_rate, detection_rate, alert_threshold, is_alerted, is_game_over, and a list of active_ice daemons. For its methods, increment_trace adds to the trace level up to 100 percent, dampens any attempts below zero, and checks if the alarm should trigger or if game over has been reached. dampen_trace allows reducing trace down to zero. trigger_alarm sets is_alerted to True and boosts the detection rate by fifty percent. tick advances the defensive clock, calculating extra noise if a CyberDeck with active programs is passed, updating trace progress, and executing any ICE daemons whose trigger thresholds have been met.
This setup uses polymorphism so TraceEngine can trigger any BaseIceDaemon subclass without needing hardcoded logic for each defensive tool. It also uses object composition by linking TraceEngine with CyberDeck and NetworkNode objects during surveillance ticks.

Key Accomplishments

Completed Stage 3 of the project proposal by implementing a reactive TraceEngine and modular ICE daemons.
Successfully got all 31 unit tests passing across test_node.py, test_graph.py, test_deck.py, and test_trace.py.
Verified that active cyberdeck programs generate realistic noise that accelerates detection, and that ICE countermeasures properly lock down target servers when alert thresholds are reached.

Challenges Faced

One challenge that came up was preventing countermeasure daemons from applying their effects repeatedly on every single tick once their threshold was crossed. For example, TraceAcceleratorIce kept boosting the detection rate every tick once active, causing the trace to spike to 100 percent in two steps. The way to mitigate this was to add state flags to the daemons, such as applied and has_triggered booleans, so one-time actions like increasing base detection speed or locking a server only execute once when the trigger condition is first met.

Learning Reflections

Developing TraceEngine showed how an antagonistic state machine can create realistic tension in a systems simulation. Using clear object attributes like alert thresholds and state booleans made it straightforward to test defensive escalation step by step without relying on real-time timers, keeping all tests completely deterministic and fast.




03/11/2026 - Iteration 5: Terminal User Interface and Game Session Controller

Activity Descriptions

Implemented the GameSession controller class in domain/session.py to coordinate the network topology, cyberdeck hardware, and trace engine under unified simulation rules.
Created the TerminalUI presentation class in ui/terminal.py featuring an ASCII dashboard HUD with hardware capacity meters, network topology tables, active program progress bars, and event logging.
Added interactive command handling with input validation for deploying scanners, cracking ports, exfiltrating data, aborting running programs, and advancing simulation turns.
Implemented main.py as a standalone runnable entrypoint setting up a realistic three-tier corporate network scenario for live software demonstration.
Wrote unit tests in tests/test_session.py and tests/test_ui.py covering session rules, victory and defeat states, dashboard rendering, and command parsing.

OOP Design and Implementation

In this stage, the project needed a clear separation between the simulation logic and the visual user interface.
GameSession was created as a high-level controller class to coordinate the domain models. For its attributes, it stores references to NetworkGraph, CyberDeck, and TraceEngine, alongside a turn counter, an event_log list, an exfiltrated_data list, and target_objective_ip to track the main mission goal. For its methods, deploy_scanner, deploy_brute_forcer, and deploy_extractor validate that the target IP exists and is currently reachable across exploited pivot points before loading the respective tool onto the deck. The tick method advances the cyberdeck hardware by one turn, logs any completed actions or breached firewalls, checks if the primary objective data was stolen to set is_victory to True, and steps the defensive trace engine forward.
TerminalUI was implemented in ui/terminal.py as a decoupled presentation layer. For its attributes, it holds a reference to the GameSession and a use_colors boolean flag that enables or disables ANSI colour codes. For its methods, render_bar draws ASCII capacity bars for RAM, CPU cores, program progress, and defensive trace percentage. render_dashboard constructs the visual interface by assembling the banner, hardware telemetry, network node table with colour status badges, active programs, and recent log messages. execute_command takes raw user input, tokenises arguments using shlex, runs the requested action with friendly error handling, and returns status feedback. run_interactive_loop provides the main read-eval-print loop that updates the terminal screen each turn until victory or defeat.
This architecture follows the Model-View-Controller design pattern, keeping the domain models completely unaware of terminal formatting while GameSession manages state transitions and TerminalUI handles display and input.

Key Accomplishments

Completed Stage 4 of the project proposal by delivering a working interactive terminal dashboard and session controller.
Successfully got all 47 unit tests passing across test_node.py, test_graph.py, test_deck.py, test_trace.py, test_session.py, and test_ui.py.
Created a ready-to-run main.py entrypoint that can be demonstrated live in a terminal without requiring any third-party external dependencies.

Challenges Faced

One challenge that came up was managing user input parsing and error reporting during interactive play. If a user entered invalid IP addresses, malformed port numbers, or attempted to crack an undiscovered server, unhandled exceptions would crash the program. The way to mitigate this was to route user inputs through execute_command with a broad try-except structure that catches KeyError, ValueError, and PermissionError exceptions. This allows the terminal UI to display helpful error guidance to the player while keeping the simulation session running smoothly.

Learning Reflections

Building the terminal interface showed the practical advantage of keeping the domain engine decoupled from the presentation code. Because the network graph, cyberdeck, and trace engine were already tested headlessly, building the UI only required formatting the existing object attributes into an ASCII layout. Testing the UI with simulated inputs also made it easy to verify the entire infiltration loop from reconnaissance to data exfiltration.




06/11/2026 - Iteration 6: Scenarios, Serialization, and State Persistence

Activity Descriptions

Implemented the ScenarioLoader class in domain/scenario.py to handle schema validation, scenario creation, and savegame file persistence.
Added validation routines to ensure scenario dictionaries verify required fields, unique node IPs, valid root nodes, and sane hardware parameters before running.
Created two playable JSON campaign files in scenarios/, Operation Iron Gate and Operation Shadow Grid, featuring multi-tiered networks and reactive ICE daemons.
Implemented full session serialization and deserialization allowing active game states, including running program progress and defensive trace levels, to be saved and restored from disk.
Integrated save, load, and scenario commands into TerminalUI and updated main.py with command-line arguments to load custom missions.
Wrote unit and integration tests in tests/test_scenario.py covering schema validation errors, scenario loading from disk, and complete round-trip save and load persistence.

OOP Design and Implementation

The final development stage required making the simulator extensible so that custom network layouts could be loaded and saved without modifying Python code.
ScenarioLoader was designed as a domain service class responsible for serialization and persistence. For its methods, validate_scenario_dict performs defensive checks on input data, verifying that node collections are non-empty, root node and target objective IPs exist in the network, and deck RAM and trace thresholds are within valid limits. load_scenario_from_dict reconstructs NetworkNode instances, adds directed edges into NetworkGraph, configures CyberDeck hardware limits, binds active ICE daemons to TraceEngine, and returns a fully initialized GameSession.
For state persistence, save_session_to_file extracts the runtime state of all four core domain classes into a nested dictionary and dumps it to a JSON file. This includes node states, open port dictionaries, active tool progress percentages, current hardware memory usage, trace escalation flags, turn counters, and the complete event log. load_session_from_file reads this file back and reconstructs the live session with identical progress, allowing an ongoing infiltration run to be paused and resumed seamlessly.
This design maintains loose coupling by isolating serialization logic within ScenarioLoader. The core domain models (NetworkNode, NetworkGraph, CyberDeck, TraceEngine) remain focused on their primary simulation responsibilities while ScenarioLoader handles JSON parsing, input validation, and object reconstruction.

Key Accomplishments

Completed Stage 5 of the project proposal, successfully finishing all planned software iterations for CyberDeck.
Implemented complete JSON scenario loading and round-trip game state persistence.
Successfully got all 52 unit and integration tests passing across all 7 test suites with zero regressions.
Verified that saved game states restore active intrusion tools with exact percentage progress and continue executing normally upon resuming.

Challenges Faced

One challenge that came up was accurately serializing and deserializing active intrusion programs running on the CyberDeck. Because Python classes cannot be directly dumped to JSON, programs needed to be serialized with their specific subclass type name, target IP, and runtime step variables. When loading the session back, the loader had to look up the reconstructed NetworkNode from the graph by its IP address and instantiate the correct subclass (PortScanner, BruteForcer, or DataExtractor) before restoring its exact progress. This was resolved by checking the program type string during deserialization and matching it to the target node object in the newly reconstructed network graph.

Learning Reflections

Implementing scenario loading and state persistence tied together all the domain classes developed across previous iterations. It demonstrated how proper object-oriented design and encapsulation make saving and restoring system state straightforward, as each class manages its own discrete attributes. Having external JSON scenario files also makes the simulator much easier to demonstrate and expand with new network architectures in the future.
