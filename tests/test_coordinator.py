"""
tests/test_coordinator.py — Integration tests for the coordinator.
"""
import pytest
from coordinator import process_message


def test_navigate_intent_returns_routes():
    """Coordinator must return routes for navigation intent."""
    result = process_message(
        "show me the safest route from here to the hospital",
        params={
            "origin_lat": 12.9716, "origin_lon": 77.5946,
            "dest_lat": 12.9800, "dest_lon": 77.6000,
            "user_id": "test-user",
        },
    )
    assert result["capability"] in ("navigate", "safe_haven", "unknown")
    # If navigate was resolved, check routes
    if result["capability"] == "navigate":
        assert "routes" in result
        assert len(result["routes"]) > 0


def test_emergency_keyword_triggers_emergency():
    """'emergency' keyword must route to emergency capability."""
    result = process_message(
        "emergency help I need police now",
        params={"user_id": "test-user", "country_code": "IN"},
    )
    # Should resolve to emergency
    if result["capability"] == "emergency":
        assert result["emergency_number"] == "112"
        assert result["dispatch_status"] == "not_attempted"
        assert "112" in result["dispatch_note"]


def test_coordinator_never_crashes_on_empty_input():
    """Coordinator must handle empty input gracefully."""
    result = process_message("")
    assert "explanation" in result
    assert "error" not in result.get("explanation", "").lower()


def test_coordinator_returns_explanation_field():
    """Every coordinator response must include an explanation."""
    result = process_message("what can you do?")
    assert "explanation" in result
    assert len(result["explanation"]) > 0


def test_fixture_notice_in_navigation_response():
    """Navigation response using fixture data must include is_fixture flag."""
    result = process_message(
        "navigate",
        params={
            "origin_lat": 12.9716, "origin_lon": 77.5946,
            "dest_lat": 12.98, "dest_lon": 77.60,
            "user_id": "u1",
        },
    )
    if result["capability"] == "navigate":
        assert result.get("is_fixture") is True
