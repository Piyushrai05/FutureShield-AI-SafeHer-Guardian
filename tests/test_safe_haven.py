"""
tests/test_safe_haven.py — Tests for Capability 3: Safe Haven Discovery.
"""
import pytest
from models.safety import Location, SafeHaven
from capabilities.safe_haven import find_safe_havens


def test_fixture_havens_returned(origin):
    """Fixture provider must return candidate safe havens."""
    havens = find_safe_havens(near=origin, provider="fixture")
    assert len(havens) > 0


def test_all_havens_have_disclaimers(origin):
    """Every safe haven must have an opening hours disclaimer."""
    havens = find_safe_havens(near=origin, provider="fixture")
    for h in havens:
        assert h.opening_hours_note, f"Haven {h.name} missing opening_hours_note"
        assert "NOT" in h.opening_hours_note.upper() or "not" in h.opening_hours_note


def test_filter_by_type(origin):
    """Filtering by place_type must return only matching types."""
    havens = find_safe_havens(
        near=origin,
        place_types=[SafeHaven.PlaceType.HOSPITAL],
        provider="fixture",
    )
    for h in havens:
        assert h.place_type == SafeHaven.PlaceType.HOSPITAL


def test_max_results_respected(origin):
    """max_results must be respected."""
    havens = find_safe_havens(near=origin, max_results=2, provider="fixture")
    assert len(havens) <= 2


def test_all_havens_have_source_caveat(origin):
    """All fixture havens must have a source_caveat."""
    havens = find_safe_havens(near=origin, provider="fixture")
    for h in havens:
        assert h.source_caveat, f"Haven {h.name} missing source_caveat"


def test_unknown_provider_raises(origin):
    """Unknown provider must raise ValueError."""
    with pytest.raises(ValueError):
        find_safe_havens(near=origin, provider="unknown_provider")
