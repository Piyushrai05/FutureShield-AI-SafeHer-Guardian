"""
tests/test_rerouting.py — Tests for Capability 6: Intelligent Rerouting.
"""
import pytest
from models.safety import (
    Location, HazardReport, HazardType, DataSource, RouteOption, NavigationRequest
)
from capabilities.rerouting import evaluate_reroute


def _make_nav_request(origin, destination):
    return NavigationRequest(
        origin=origin, destination=destination, user_id="test-user"
    )


def _make_route(route_id="r1"):
    return RouteOption(
        route_id=route_id,
        description="Test route",
        distance_km=3.0,
        safety_score=7.5,
        source=DataSource.FIXTURE,
        data_caveat="[FIXTURE]",
    )


def test_fixture_hazard_does_not_trigger_reroute(origin, destination):
    """Fixture hazards must NOT trigger rerouting (not credible for live use)."""
    req = _make_nav_request(origin, destination)
    current = _make_route()
    hazard = HazardReport(
        hazard_type=HazardType.POOR_LIGHTING,
        description="Fixture hazard",
        source=DataSource.FIXTURE,
        age_minutes=10.0,
    )
    new_nav, explanation = evaluate_reroute(req, current, hazard, provider="fixture")
    # Should return original route unchanged
    assert current.route_id in [r.route_id for r in new_nav.routes]
    assert "REJECTED" in explanation or "not triggered" in explanation.lower()


def test_stale_hazard_does_not_trigger_reroute(origin, destination, stale_hazard):
    """Stale hazards (>120 min old) must not trigger rerouting."""
    req = _make_nav_request(origin, destination)
    current = _make_route()
    stale_hazard.source = DataSource.USER_REPORT  # Make it a non-fixture source
    new_nav, explanation = evaluate_reroute(req, current, stale_hazard, provider="fixture")
    assert "stale" in explanation.lower() or "REJECTED" in explanation


def test_verified_live_hazard_triggers_reroute(origin, destination):
    """A verified live hazard should trigger rerouting."""
    req = _make_nav_request(origin, destination)
    current = _make_route("current-route")
    hazard = HazardReport(
        hazard_type=HazardType.ROAD_CLOSURE,
        description="Live road closure",
        source=DataSource.LIVE_API,
        verified=True,
        age_minutes=5.0,
    )
    new_nav, explanation = evaluate_reroute(req, current, hazard, provider="fixture")
    assert "rerouting triggered" in explanation.lower() or "reroute" in explanation.lower()


def test_reroute_response_has_routes(origin, destination):
    """Reroute response must always include at least one route."""
    req = _make_nav_request(origin, destination)
    current = _make_route()
    hazard = HazardReport(
        hazard_type=HazardType.FLOOD,
        description="Live flood",
        source=DataSource.LIVE_API,
        verified=True,
        age_minutes=1.0,
    )
    new_nav, _ = evaluate_reroute(req, current, hazard, provider="fixture")
    assert len(new_nav.routes) > 0
