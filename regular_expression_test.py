import pytest
from hypothesis import given, strategies as st
from regular_expression import RegexInterpreter


# Standard Unit Testing (Deterministic Assertions)
def test_standard_literal_flows() -> None:
    """Verifies deterministic sequence flows for exact text matching."""
    engine = RegexInterpreter("abc")
    assert engine.match("abc") is True
    assert engine.match("ab") is False
    # Prefix match logic: "abc" is a valid prefix of "abcd"
    assert engine.match("abcd") is True


def test_standard_wildcards_and_closures() -> None:
    """Validates structural behavior of closure loops and wildcards."""
    engine = RegexInterpreter("a.c*")
    assert engine.match("abc") is True
    assert engine.match("axcccc") is True
    # Closure logic: 'c' can appear zero times, making "ab" perfectly valid.
    assert engine.match("ab") is True


def test_standard_character_classes() -> None:
    """Validates character wildcards parsing sequences successfully."""
    engine = RegexInterpreter(r"\d+\w")
    assert engine.match("1a") is True
    assert engine.match("9999_") is True
    assert engine.match("a1") is False


def test_aop_type_enforcement_boundary() -> None:
    """Ensures that AOP safety proxy triggers explicit TypeError blocks."""
    engine = RegexInterpreter("secure")
    with pytest.raises(TypeError):
        # Intentionally passing an integer to verify AOP boundaries
        engine.match(42)  # type: ignore


# Property-Based Testing (Hypothesis Generative Invariants)
@given(
    st.text(
        alphabet=st.characters(
            whitelist_categories=("Nd",)  # type: ignore[arg-type]
        ),
        min_size=1,
    )
)
def test_pbt_digit_class_invariants(text: str) -> None:
    """Enforces mathematical invariant properties for digits under closure."""
    engine = RegexInterpreter(r"\d+")
    # Invariant: Any stream built purely of digits must yield True
    assert engine.match(text) is True


@given(st.text())
def test_pbt_fuzz_engine_stability(text: str) -> None:
    """Fuzzes state machines globally to guarantee crash-free runtime loops."""
    engine = RegexInterpreter(".*")
    # Invariant: The engine must process arbitrary fuzz inputs without crashing
    try:
        engine.match(text)
    except Exception as exc:
        pytest.fail(f"NFA Engine crashed unexpectedly during fuzz test: {exc}")
