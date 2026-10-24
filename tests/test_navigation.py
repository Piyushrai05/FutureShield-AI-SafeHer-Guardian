"""
tests/test_navigation.py — Tests for Capability 1: Safety-First Navigation.
"""
import pytest
from models.safety import NavigationRequest, DataSource
from capabilities.navigation import get_safe_routes


def test_fixture_routes_returned(origin, destination):
    """Should return routes clearly labelled as fixture data."""
    req = NavigationRequest(
        origin=origin,
        destination=destination,
        user_id="test-user",
        prefer_safety=True,
        max_routes=3,
    )
    result = get_safe_routes(req, provider="fixture")

    assert result.is_fixture is True
    assert len(result.routes) > 0
    assert result.recommended_route_id is not None
    assert result.data_source == DataSource.FIXTURE


def test_routes_sorted_by_safety(origin, destination):
    """Routes should be sorted highest safety score first when prefer_safety=True."""
    req = NavigationRequest(
        origin=origin,
        destination=destination,
        user_id="test-user",
        prefer_safety=True,
        max_routes=3,
    )
    result = get_safe_routes(req, provider="fixture")
    scores = [r.safety_score for r in result.routes]
    assert scores == sorted(scores, reverse=True), "Routes not sorted by safety score"


def test_max_routes_respected(origin, destination):
    """max_routes parameter must be respected."""
    req = NavigationRequest(
        origin=origin,
        destination=destination,
        user_id="test-user",
        prefer_safety=True,
        max_routes=2,
    )
    result = get_safe_routes(req, provider="fixture")
    assert len(result.routes) <= 2


def test_all_fixture_routes_have_caveats(origin, destination):
    """Every fixture route must have a non-empty data_caveat."""
    req = NavigationRequest(
        origin=origin,
        destination=destination,
        user_id="test-user",
    )
    result = get_safe_routes(req, provider="fixture")
    for route in result.routes:
        assert route.data_caveat, f"Route {route.route_id} missing data_caveat"


def test_unknown_provider_raises(origin, destination):
    """Unknown provider should raise ValueError."""
    req = NavigationRequest(
        origin=origin, destination=destination, user_id="u1"
    )
    with pytest.raises(ValueError):
        get_safe_routes(req, provider="nonexistent_provider")


def test_fixture_duration_is_none(origin, destination):
    """Fixture routes must NOT invent travel times (duration must be None)."""
    req = NavigationRequest(
        origin=origin, destination=destination, user_id="u1"
    )
    result = get_safe_routes(req, provider="fixture")
    for r in result.routes:
        assert r.duration_min_estimate is None, (
            f"Route {r.route_id} has invented duration {r.duration_min_estimate}"
        )
