# GROUP-7 - lab 3 - variant 7

This project implements a subset of a Regular Expression execution engine
based on the Finite State Machine (FSM) Model of Computation (Variant 7).
It parses regular expressions into Non-deterministic Finite Automata (NFA)
utilizing Thompson's construction and provides pattern matching and
visualization capabilities.

## Project structure

- `regular_expression.py` -- Core implementation of the Regex MoC. Contains
  the `RegexInterpreter` engine, Thompson construction logic, FSM node
  representations, GraphViz visualization (`visualize` method), and
  Aspect-Oriented Programming (AOP) data validation decorators. Stateless
  FSM execution.
- `regular_expression_test.py` -- Quality assurance suite. Contains standard
  deterministic unit tests (pytest) validating prefix matching semantics,
  and Property-Based Tests (PBT) using Hypothesis to guarantee mathematical
  invariants and engine stability.

## Features

- **Regex Compilation**: Parses literal characters, wildcards (`.`), character
  classes (`\d`, `\w`, `\s`), and closures (`*`, `+`) into FSM graphs.
- **Prefix Matching Engine**: Fully adheres to Python's standard `re.match`
  sticky prefix semantics via Epsilon-closure wavefront expansion.
- **AOP Data Control**: Implements non-invasive input data validation
  (`@enforce_string_inputs`) using decorators to ensure strict string-type
  boundaries.
- **FSM Visualization**: Generates legal GraphViz DOT notation to visualize
  the internal states, transition paths, and accepting nodes of the
  compiled NFA.
- **PBT**: Includes generative invariant testing
  (`test_pbt_digit_class_invariants` and `test_pbt_fuzz_engine_stability`)
  to ensure crash-free execution under extreme boundary conditions.

## Contribution

- Your Name (1661342449@qq.com) -- Architectural design, FSM
  compilation engine, AOP implementation, and test coverage.

## Changelog

- 25.05.2026 - 2
  Refactor execution engine to properly support standard prefix
  matching semantics (`re.match`).
  Resolve static typing invariance conflicts by removing unnecessary
  generic abstractions (`TypeVar` T).
- 24.05.2026 - 1
  Implement GraphViz visualization export.
  Add Hypothesis property-based testing and baseline deterministic
  unit tests.
- 23.05.2026 - 0
  Initial structure. Implement Thompson's construction and AOP
  validation decorators.

## Design notes

- **Static Typing and Invariance Constraints**: Initially, the FSM nodes
  and Matchers were designed using Python Generics (`TypeVar('T',
  bound=str)`). However, strict static analysis (`Pylance`/`mypy`)
  revealed an Invariance Conflict: Python string slicing dynamically returns
  a base `str`, which cannot be safely injected into a strict `Generic[T]`
  bound without risking subtype pollution. To align with engineering
  pragmatism, Generics were completely stripped from the engine,
  effectively locking the domain type to `str`, resulting in zero static
  analysis warnings and high cohesion.
- **Thompson's Construction State Chain**: To ensure accurate concatenation
  matching, the graph concatenation algorithm dynamically strips the
  `is_accepting` status from intermediate fragment nodes, transferring the
  acceptance baton exclusively to the absolute final node of the
  expression.
- **Prefix Matching vs. Full Matching**: To align with standard industrial
  implementations, the execution engine evaluates using a "sticky prefix
  match" logic. As the input text stream is consumed, if the expanding
  Epsilon-closure wavefront encounters an accepting state at *any*
  intermediate step, the success is locked in, matching the behavior of
  `re.match("abc", "abcd") -> True`.
- **AOP Metadata Retention**: The input validation decorator uses
  `typing.cast` and `@functools.wraps` to bypass type checker metadata loss,
  ensuring that the wrapped API functions retain their exact signatures while
  gaining robust runtime type safety.
