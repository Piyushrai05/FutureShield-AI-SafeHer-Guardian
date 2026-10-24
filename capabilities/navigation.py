"""
capabilities/navigation.py — Capability 1: Safety-First Navigation.

Compares route alternatives using provider results or clearly-labelled fixtures.
NEVER invents live routes or travel times.
"""
from __future__ import annotations

import uuid
import logging
from typing import Optional

from models.safety import (
    Location,
    RouteOption,
    NavigationRequest,
    NavigationResponse,
    HazardReport,
    HazardType,
    DataSource,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Fixture data — clearly labelled, never presented as live data
# ─────────────────────────────────────────────────────────────
_FIXTURE_CAVEAT = (
    "[FIXTURE DATA] This route was generated from a static test dataset. "
    "Do NOT use for real navigation. Real provider not configured."
)


def _fixture_routes(origin: Location, destination: Location) -> list[RouteOption]:
    """Return labelled fixture routes. Used when ROUTING_PROVIDER=fixture."""
    return [
        RouteOption(
            route_id="fixture-r1",
            description="Main road via well-lit commercial area (FIXTURE)",
            distance_km=3.2,
            duration_min_estimate=None,  # Unknown without live data
            safety_score=8.0,
            hazards=[],
            source=DataSource.FIXTURE,
            data_caveat=_FIXTURE_CAVEAT,
        ),
        RouteOption(
            route_id="fixture-r2",
            description="Shortcut via residential lanes — limited lighting (FIXTURE)",
            distance_km=2.1,
            duration_min_estimate=None,
            safety_score=4.5,
            hazards=[
                HazardReport(
                    hazard_type=HazardType.POOR_LIGHTING,
                    description="Section reported as poorly lit (FIXTURE — not verified)",
                    source=DataSource.FIXTURE,
                    verified=False,
                )
            ],
            source=DataSource.FIXTURE,
            data_caveat=_FIXTURE_CAVEAT,
        ),
        RouteOption(
            route_id="fixture-r3",
            description="Longer but well-monitored road via transit stop (FIXTURE)",
            distance_km=4.8,
            duration_min_estimate=None,
            safety_score=9.0,
            hazards=[],
            source=DataSource.FIXTURE,
            data_caveat=_FIXTURE_CAVEAT,
        ),
    ]


def _score_sort_key(route: RouteOption) -> float:
    """Higher safety score first."""
    return -route.safety_score


def get_safe_routes(request: NavigationRequest, provider: str = "fixture") -> NavigationResponse:
    """
    Main entry point for Capability 1.

    Parameters
    ----------
    request  : NavigationRequest
    provider : str — "fixture" | "ors" | "here"
               Only "fixture" is implemented without external API keys.

    Returns
    -------
    NavigationResponse with clearly-labelled data source.
    """
    request_id = str(uuid.uuid4())
    logger.info(f"[navigation] Routing request {request_id} provider={provider}")

    if provider == "fixture":
        routes = _fixture_routes(request.origin, request.destination)
        is_fixture = True
    elif provider in ("ors", "here"):
        # Real provider integration placeholder.
        # Requires ROUTING_API_KEY in .env.
        logger.warning(
            f"[navigation] Provider '{provider}' selected but not yet implemented. "
            "Falling back to fixture data."
        )
        routes = _fixture_routes(request.origin, request.destination)
        is_fixture = True
    else:
        raise ValueError(f"Unknown routing provider: {provider!r}")

    # Sort by safety score (descending) when preference is safety
    if request.prefer_safety:
        routes = sorted(routes, key=_score_sort_key)

    routes = routes[: request.max_routes]

    recommended = routes[0].route_id if routes else None

    explanation = (
        f"Found {len(routes)} route(s). "
        + (f"Recommended: {routes[0].description}" if routes else "No routes found.")
        + (f" [Source: {provider.upper()} FIXTURE — not live data]" if is_fixture else "")
    )

    return NavigationResponse(
        request_id=request_id,
        routes=routes,
        recommended_route_id=recommended,
        explanation=explanation,
        data_source=DataSource.FIXTURE if is_fixture else DataSource.LIVE_API,
        is_fixture=is_fixture,
    )
