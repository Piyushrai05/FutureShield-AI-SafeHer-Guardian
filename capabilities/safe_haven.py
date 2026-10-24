"""
capabilities/safe_haven.py — Capability 3: Safe Haven Discovery.

Finds candidate hospitals, pharmacies, petrol stations, police facilities.
NEVER claims opening hours or assistance availability without supporting evidence.
"""
from __future__ import annotations

import uuid
import logging
from typing import Optional

from models.safety import Location, SafeHaven, DataSource

logger = logging.getLogger(__name__)

_FIXTURE_CAVEAT = (
    "[FIXTURE DATA] This location was generated from a static test dataset. "
    "Opening hours and availability NOT verified. Do NOT rely on this without live confirmation."
)

_OPENING_HOURS_DISCLAIMER = (
    "Opening hours have NOT been verified from a live source. "
    "Confirm availability before travelling to this location."
)


def _fixture_safe_havens(
    near: Location,
    place_types: Optional[list[SafeHaven.PlaceType]] = None,
    max_results: int = 5,
) -> list[SafeHaven]:
    """Return clearly labelled fixture safe havens."""
    all_fixtures = [
        SafeHaven(
            place_id="fix-h1",
            name="Government General Hospital (FIXTURE)",
            place_type=SafeHaven.PlaceType.HOSPITAL,
            location=Location(lat=near.lat + 0.003, lon=near.lon + 0.004, label="General Hospital"),
            distance_km=0.6,
            opening_hours_note=_OPENING_HOURS_DISCLAIMER,
            phone="112",
            source=DataSource.FIXTURE,
            source_caveat=_FIXTURE_CAVEAT,
        ),
        SafeHaven(
            place_id="fix-p1",
            name="Apollo Pharmacy (FIXTURE)",
            place_type=SafeHaven.PlaceType.PHARMACY,
            location=Location(lat=near.lat - 0.002, lon=near.lon + 0.001, label="Pharmacy"),
            distance_km=0.3,
            opening_hours_note=_OPENING_HOURS_DISCLAIMER,
            phone=None,
            source=DataSource.FIXTURE,
            source_caveat=_FIXTURE_CAVEAT,
        ),
        SafeHaven(
            place_id="fix-ps1",
            name="Local Police Station (FIXTURE)",
            place_type=SafeHaven.PlaceType.POLICE,
            location=Location(lat=near.lat + 0.007, lon=near.lon - 0.002, label="Police Station"),
            distance_km=1.1,
            opening_hours_note=_OPENING_HOURS_DISCLAIMER,
            phone="100",
            source=DataSource.FIXTURE,
            source_caveat=_FIXTURE_CAVEAT,
        ),
        SafeHaven(
            place_id="fix-g1",
            name="Indian Oil Petrol Station (FIXTURE)",
            place_type=SafeHaven.PlaceType.PETROL_STATION,
            location=Location(lat=near.lat - 0.005, lon=near.lon - 0.003, label="Petrol Station"),
            distance_km=0.8,
            opening_hours_note=_OPENING_HOURS_DISCLAIMER,
            source=DataSource.FIXTURE,
            source_caveat=_FIXTURE_CAVEAT,
        ),
        SafeHaven(
            place_id="fix-f1",
            name="Fire & Rescue Station (FIXTURE)",
            place_type=SafeHaven.PlaceType.FIRE_STATION,
            location=Location(lat=near.lat + 0.010, lon=near.lon + 0.005, label="Fire Station"),
            distance_km=1.5,
            opening_hours_note=_OPENING_HOURS_DISCLAIMER,
            phone="101",
            source=DataSource.FIXTURE,
            source_caveat=_FIXTURE_CAVEAT,
        ),
    ]

    if place_types:
        all_fixtures = [h for h in all_fixtures if h.place_type in place_types]

    # Sort by distance
    all_fixtures.sort(key=lambda h: h.distance_km or 9999)
    return all_fixtures[:max_results]


def find_safe_havens(
    near: Location,
    place_types: Optional[list[SafeHaven.PlaceType]] = None,
    max_results: int = 5,
    provider: str = "fixture",
) -> list[SafeHaven]:
    """
    Main entry point for Capability 3.

    Parameters
    ----------
    near         : User's current location
    place_types  : Filter by type (None = all types)
    max_results  : Maximum number of results to return
    provider     : "fixture" | "overpass" | "google"

    Returns
    -------
    List of SafeHaven objects with caveat strings; never stripped of disclaimers.
    """
    logger.info(f"[safe_haven] Finding safe havens near ({near.lat:.4f},{near.lon:.4f}) provider={provider}")

    if provider == "fixture":
        havens = _fixture_safe_havens(near, place_types, max_results)
    elif provider in ("overpass", "google"):
        logger.warning(
            f"[safe_haven] Provider '{provider}' requires POI_API_KEY — falling back to fixture."
        )
        havens = _fixture_safe_havens(near, place_types, max_results)
    else:
        raise ValueError(f"Unknown POI provider: {provider!r}")

    logger.info(f"[safe_haven] Returning {len(havens)} candidates")
    return havens
