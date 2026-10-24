"""
tests/conftest.py — Shared pytest fixtures.
"""
import sys
import os
import pytest

# Add project root to path for all tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def origin():
    from models.safety import Location
    return Location(lat=12.9716, lon=77.5946, label="Test Origin")


@pytest.fixture
def destination():
    from models.safety import Location
    return Location(lat=12.9800, lon=77.6000, label="Test Destination")


@pytest.fixture
def sample_hazard():
    from models.safety import HazardReport, HazardType, DataSource
    return HazardReport(
        hazard_type=HazardType.POOR_LIGHTING,
        description="Test hazard: poorly lit street",
        source=DataSource.FIXTURE,
        verified=False,
        age_minutes=30.0,
    )


@pytest.fixture
def stale_hazard():
    from models.safety import HazardReport, HazardType, DataSource
    return HazardReport(
        hazard_type=HazardType.ROAD_CLOSURE,
        description="Test stale hazard",
        source=DataSource.USER_REPORT,
        verified=False,
        age_minutes=150.0,  # Stale: > 120 min
    )
