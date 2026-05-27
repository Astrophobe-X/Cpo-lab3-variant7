import functools
import logging
from collections import deque
from typing import (
    Any,
    Callable,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    cast,
)

# Setup standard Python logger for transparent execution tracking
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("RegexMoC")

# Type variable specifically for capturing wrapped function signatures in AOP
F = TypeVar("F", bound=Callable[..., Any])


# Aspect-Oriented Programming (AOP) Input Data Control
def enforce_string_inputs(func: F) -> F:
    """AOP Advice: Ensures strict validation for string API parameters."""
    func_name = getattr(func, "__name__", "unnamed_callable")

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Validate positional arguments, skipping the 'self' context
        for idx, arg in enumerate(args[1:], start=1):
            if not isinstance(arg, str):
                raise TypeError(
                    f"Argument at index {idx} in {func_name} "
                    f"must be str, got {type(arg).__name__}"
                )
        # Validate explicit keyword arguments
        for key, val in kwargs.items():
            if not isinstance(val, str):
                raise TypeError(
                    f"Keyword argument '{key}' in {func_name} "
                    f"must be str, got {type(val).__name__}"
                )
        return func(*args, **kwargs)

    # Cast to satisfy strict static type checkers regarding decorator return
    return cast(F, wrapper)


# Automaton Component Design & Delegation Pattern
class CharacterMatcher:
    """Base interface for behavioral character evaluation rules."""

    def matches(self, char: str) -> bool:
        raise NotImplementedError


class SpecificCharMatcher(CharacterMatcher):
    """Matches a singular exact literal character token."""

    def __init__(self, char: str) -> None:
        self.char: str = char

    def matches(self, char: str) -> bool:
        return char == self.char


class RegexClassMatcher(CharacterMatcher):
    """Evaluates standard regex wildcard classes like digits or dots."""

    def __init__(self, class_type: str) -> None:
        self.class_type: str = class_type

    def matches(self, char: str) -> bool:
        if not char:
            return False
        if self.class_type == "d":
            return char.isdigit()
        if self.class_type == "w":
            return char.isalnum() or char == "_"
        if self.class_type == "s":
            return char.isspace()
        if self.class_type == ".":
            return char != "\n"
        return False


class NFAState:
    """Discrete state graph vertex inside the operational automation map."""

    def __init__(self, state_id: int, is_accepting: bool = False) -> None:
        self.state_id: int = state_id
        self.is_accepting: bool = is_accepting
        self.transitions: List[Tuple["NFAState", CharacterMatcher]] = []
        self.epsilon_transitions: List["NFAState"] = []

    def add_transition(
        self, to_state: "NFAState", matcher: CharacterMatcher
    ) -> None:
        """Connects states via a targeted literal or class filter rule."""
        self.transitions.append((to_state, matcher))

    def add_epsilon(self, to_state: "NFAState") -> None:
        """Connects states via an instantaneous zero-cost epsilon link."""
        self.epsilon_transitions.append(to_state)


class NFAFragment:
    """Encapsulates a bounded subgraph matching component definition."""

    def __init__(self, start: NFAState, accept: NFAState) -> None:
        self.start_state: NFAState = start
        self.accept_state: NFAState = accept


# Core Regular Expression Interpreter Engine
class RegexInterpreter:
    """Engine responsible for pattern compilation and execution handling."""

    @enforce_string_inputs
    def __init__(self, pattern: str) -> None:
        self.pattern: str = pattern
        self.state_counter: int = 0
        self.start_fragment: Optional[NFAFragment] = None
        self._all_states: List[NFAState] = []
        self._compile()

    def _create_state(self, is_accepting: bool = False) -> NFAState:
        """Instantiates a new tracked vertex within the memory map."""
        state = NFAState(self.state_counter, is_accepting)
        self.state_counter += 1
        self._all_states.append(state)
        return state

    def _compile(self) -> None:
        """Constructs a complex FSM structure via Thompson paradigms."""
        logger.info("Compiling regular expression: '%s'", self.pattern)
        fragments: List[NFAFragment] = []
        idx = 0

        try:
            while idx < len(self.pattern):
                char = self.pattern[idx]

                if char == "\\":
                    idx += 1
                    class_char = self.pattern[idx]
                    s1 = self._create_state()
                    s2 = self._create_state()
                    s1.add_transition(s2, RegexClassMatcher(class_char))
                    fragments.append(NFAFragment(s1, s2))
                elif char == ".":
                    s1 = self._create_state()
                    s2 = self._create_state()
                    dot_char = self.pattern[idx]
                    s1.add_transition(s2, RegexClassMatcher(dot_char))
                    fragments.append(NFAFragment(s1, s2))
                elif char in ("*", "+"):
                    if not fragments:
                        raise ValueError("No antecedent token found")
                    last_frag = fragments.pop()
                    s1 = self._create_state()
                    s2 = self._create_state()

                    if char == "*":
                        s1.add_epsilon(last_frag.start_state)
                        s1.add_epsilon(s2)
                        last_frag.accept_state.add_epsilon(
                            last_frag.start_state
                        )
                        last_frag.accept_state.add_epsilon(s2)
                    else:
                        s1.add_epsilon(last_frag.start_state)
                        last_frag.accept_state.add_epsilon(
                            last_frag.start_state
                        )
                        last_frag.accept_state.add_epsilon(s2)
                    fragments.append(NFAFragment(s1, s2))
                else:
                    s1 = self._create_state()
                    s2 = self._create_state()
                    s1.add_transition(s2, SpecificCharMatcher(char))
                    fragments.append(NFAFragment(s1, s2))
                idx += 1

            if not fragments:
                empty_s = self._create_state(is_accepting=True)
                self.start_fragment = NFAFragment(empty_s, empty_s)
                return

            # Chain sequential fragments; only the final node is accepting
            for i in range(len(fragments) - 1):
                fragments[i].accept_state.is_accepting = False
                fragments[i].accept_state.add_epsilon(
                    fragments[i + 1].start_state
                )

            self.start_fragment = NFAFragment(
                fragments[0].start_state, fragments[-1].accept_state
            )
            self.start_fragment.accept_state.is_accepting = True

        except Exception as err:
            logger.error("FSM construction aborted: '%s'", str(err))
            raise RuntimeError(f"Compilation abort: {str(err)}") from err

    def _get_epsilon_closure(self, states: Set[NFAState]) -> Set[NFAState]:
        """Processes graph reachability over unconsumed epsilon hops."""
        closure = set(states)
        queue = deque(states)
        while queue:
            current = queue.popleft()
            for neighbor in current.epsilon_transitions:
                if neighbor not in closure:
                    closure.add(neighbor)
                    queue.append(neighbor)
        return closure

    @enforce_string_inputs
    def match(self, text: str) -> bool:
        """Evaluates pattern matching utilizing prefix semantics (re.match)."""
        assert self.start_fragment is not None
        current_states = self._get_epsilon_closure(
            {self.start_fragment.start_state}
        )

        match_found = any(s.is_accepting for s in current_states)

        for char in text:
            if not current_states:
                break

            next_states: Set[NFAState] = set()
            for state in current_states:
                for dest, matcher in state.transitions:
                    if matcher.matches(char):
                        next_states.add(dest)

            current_states = self._get_epsilon_closure(next_states)

            if any(s.is_accepting for s in current_states):
                match_found = True

        return match_found

    # 4. Automation Model Visualization Implementation
    def visualize(self) -> str:
        """Generates legal GraphViz DOT code for the NFA state diagram."""
        dot_lines = [
            "digraph G {",
            "    rankdir=LR;",
            "    node [shape=circle];",
        ]
        accept_states = [s for s in self._all_states if s.is_accepting]

        # Explicitly declare accepting double-circle states
        if accept_states:
            labels = " ".join([f"n_{s.state_id}" for s in accept_states])
            dot_lines.append(f"    node [shape=doublecircle]; {labels};")
            dot_lines.append("    node [shape=circle];")

        # Populate structural transitions across vectors
        for state in self._all_states:
            for dest, matcher in state.transitions:
                label = getattr(
                    matcher, "char", getattr(matcher, "class_type", "?")
                )
                if label == "\\":
                    label = "\\\\"
                dot_lines.append(
                    f"    n_{state.state_id} -> n_{dest.state_id} "
                    f'[label="{label}"];'
                )
            for dest in state.epsilon_transitions:
                dot_lines.append(
                    f"    n_{state.state_id} -> n_{dest.state_id} "
                    '[label="&epsilon;"];'
                )
        dot_lines.append("}")
        return "\n".join(dot_lines)

    def generate_transition_table(self) -> str:
        """Generates a text-formatted State Transition Table for the FSM."""
        table_lines = [
            f"State Transition Table for Regex Pattern: '{self.pattern}'",
            "-" * 65,
            f"{'Source State':<15} | {'Trigger / Matcher':<25} | {'Target State'}",
            "-" * 65,
        ]

        for state in self._all_states:
            state_label = f"State {state.state_id}"
            if state.is_accepting:
                state_label += " (Accept)"

            # Print standard token-driven edges
            for dest, matcher in state.transitions:
                trigger = getattr(
                    matcher, "char", getattr(matcher, "class_type", "?")
                )
                trigger_label = f"Symbol: '{trigger}'"
                table_lines.append(
                    f"{state_label:<15} | {trigger_label:<25} | State {dest.state_id}"
                )

            # Print zero-cost instantaneous links
            for dest in state.epsilon_transitions:
                table_lines.append(
                    f"{state_label:<15} | {'Epsilon (ε)':<25} | State {dest.state_id}"
                )

        return "\n".join(table_lines)
