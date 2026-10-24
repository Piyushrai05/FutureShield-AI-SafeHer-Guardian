"""
tests/test_safety_analysis.py — Tests for Capability 2: Safety Evidence Analysis.
"""
import pytest
from models.safety import Location, DataSource
from capabilities.safety_analysis import analyse_safety


def test_missing_data_flagged():
    """Missing data items must appear in the result — never silently dropped."""
    loc = Location(lat=12.97, lon=77.59)
    result = analyse_safety(
        location=loc,
        hazards=[],
        staffed_places_nearby=0,
        emergency_access_confirmed=False,
        data_source=DataSource.FIXTURE,
        data_timestamp=None,
    )
    assert len(result.missing_data_items) > 0, "Missing data should be flagged"
    assert "data_timestamp" in " ".join(result.missing_data_items)
    assert "emergency_access" in " ".join(result.missing_data_items)


def test_score_decreases_with_verified_hazard(sample_hazard, origin):
    """Verified hazard must lower the safety score."""
    sample_hazard.verified = True
    no_hazard = analyse_safety(
        location=origin, hazards=[], staffed_places_nearby=0,
        emergency_access_confirmed=False,
    )
    with_hazard = analyse_safety(
        location=origin, hazards=[sample_hazard], staffed_places_nearby=0,
        emergency_access_confirmed=False,
    )
    assert with_hazard.overall_score < no_hazard.overall_score


def test_score_never_exceeds_ten(origin):
    """Safety score must be capped at 10.0."""
    result = analyse_safety(
        location=origin, hazards=[], staffed_places_nearby=10,
        emergency_access_confirmed=True, data_source=DataSource.LIVE_API,
        data_timestamp=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
    )
    assert result.overall_score <= 10.0


def test_score_never_below_zero(origin):
    """Safety score must never go below 0.0."""
    from models.safety import HazardReport, HazardType
    hazards = [
        HazardReport(
            hazard_type=HazardType.CRIME_REPORT,
            description=f"Hazard {i}",
            verified=True, age_minutes=10.0,
        )
        for i in range(20)
    ]
    result = analyse_safety(location=origin, hazards=hazards, staffed_places_nearby=0)
    assert result.overall_score >= 0.0


def test_fixture_source_appears_in_missing_data(origin):
    """When DataSource is FIXTURE, it must be flagged in missing_data_items."""
    result = analyse_safety(
        location=origin, hazards=[], staffed_places_nearby=1,
        data_source=DataSource.FIXTURE,
    )
    assert any("live_data" in item or "FIXTURE" in item for item in result.missing_data_items), (
        "Fixture source must appear in missing_data_items"
    )
