from typing import Callable, Dict, List, Optional, Tuple

class State:
    """ 
    Represents a state in a state machine. 
    
    Each state has an entry and exit action that are executed when the state is entered and exited, respectively. 
    The entry and exit actions default to no action and can be overridden by passing a function to the constructor.
    """
    
    def __init__(self, name: str, entry_action: Optional[Callable[[], None]] = None, exit_action: Optional[Callable[[], None]] = None):
        """
        __init__ method for State class.

        Arguments:
            name {str} -- The name of the state.

        Keyword Arguments:
            entry_action {() -> None} -- Entry action (default: empty function)
            exit_action {() -> None} -- Exit action (default: empty function)
        """
        self.name: str = name
        self.entry_action = entry_action or self._no_action
        self.exit_action = exit_action or self._no_action

    def _no_action(self) -> None:
        pass

    def __repr__(self) -> str:
        return self.name

class StateMachine:
    """
    Represents a state machine that manages states and transitions between them.
    
    The state machine has a current state and a dictionary of states and transitions.
    The state machine can add states, add transitions between states, set the current state, and update the state machine.
    """
    
    def __init__(self, initial_state: State):
        """
        __init__ method for StateMachine class.

        Arguments:
            initial_state {State} -- The initial state of the state machine.
        """
        
        self.states: Dict[str, State] = {}
        self.transitions: Dict[str, List[Tuple[str, Callable[[], bool]]]] = {}
        self.current_state: State = initial_state
        self.previous_state: Optional[State] = None

    def add_state(self, state: State) -> None:
        """
        Adds a state to the state machine.

        Arguments:
            state {State} -- The state to add to the state machine.
        """
        
        self.states[state.name] = state

    def add_transition(self, from_state: str, to_state: str, condition) -> None:
        """
        Adds a transition between two states in the state machine.

        Arguments:
            from_state {str} -- starting state
            to_state {str} -- ending state
            condition {() -> bool} -- condition to transition from from_state to to_state
        """
        
        if from_state not in self.transitions:
            self.transitions[from_state] = []
        self.transitions[from_state].append((to_state, condition))

    def set_state(self, state_name: str) -> None:
        """
        Sets the current state of the state machine to a new state.
        This method also executes the exit action of the current state and the entry action of the new state.

        Arguments:
            state_name {str} -- The name of the new state to set as the current state.

        Raises:
            ValueError: If the state name does not exist in the state machine.
        """
        if state_name in self.states:
            self.previous_state = self.current_state
            self.current_state.exit_action()
            self.current_state = self.states[state_name]
            self.current_state.entry_action()
        else:
            raise ValueError(f"State {state_name} does not exist in the state machine")

    def update(self) -> None:
        """
        Updates the state of the state machine based on the transitions defined.
        """
        if self.current_state.name in self.transitions:
            for (next_state, condition) in self.transitions[self.current_state.name]:
                if condition():
                    self.set_state(next_state)
                    break


if __name__ == "__main__":

    # Create states
    idle = State("Idle", lambda: print("Entering Idle State"), lambda: print("Exiting Idle State"))
    active = State("Active", lambda: print("Entering Active State"), lambda: print("Exiting Active State"))
    finished = State("Finished", lambda: print("Entering Finished State"), lambda: print("Exiting Finished State"))

    # Create state machine and add states
    sm = StateMachine(idle)
    sm.add_state(idle)
    sm.add_state(active)
    sm.add_state(finished)

    # Add transitions
    sm.add_transition("Idle", "Active", lambda: True)  # Transition from Idle to Active when condition is True
    sm.add_transition("Active", "Finished", lambda: True)  # Transition from Active to Finished when condition is True

    # Run state machine
    print(f"- Initial State: {sm.current_state}")
    sm.update()  # Should transition to Active
    print(f"- Current State: {sm.current_state}")
    sm.update()  # Should transition to Finished
    print(f"- Current State: {sm.current_state}")

