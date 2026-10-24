"""
capabilities/rerouting.py — Capability 6: Intelligent Rerouting.

Re-evaluates route alternatives when credible hazards or road closures are received.
Validates source, timestamp, and relevance before changing recommendations.
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional

from models.safety import (
    Location,
    RouteOption,
    HazardReport,
    NavigationRequest,
    NavigationResponse,
    DataSource,
    HazardType,
)
from capabilities.navigation import get_safe_routes

logger = logging.getLogger(__name__)

# Maximum age for a hazard report to be considered actionable
_MAX_HAZARD_AGE_MINUTES = 120


class RerouteReason:
    HAZARD_ON_CURRENT_ROUTE = "hazard_on_current_route"
    ROAD_CLOSURE = "road_closure"
    USER_REQUESTED = "user_requested"


def _is_hazard_credible(hazard: HazardReport) -> tuple[bool, str]:
    """
    Validate whether a hazard report is credible enough to trigger rerouting.

    Returns (is_credible: bool, reason: str)
    """
    if hazard.source == DataSource.FIXTURE:
        return False, "Fixture data — not used for live rerouting decisions"

    if hazard.age_minutes is not None and hazard.age_minutes > _MAX_HAZARD_AGE_MINUTES:
        return (
            False,
            f"Hazard is stale ({hazard.age_minutes:.0f} min old > {_MAX_HAZARD_AGE_MINUTES} min threshold)",
        )

    if not hazard.verified and hazard.source == DataSource.USER_REPORT:
        return True, "Unverified user report — rerouting as precaution (flagged)"

    if hazard.verified:
        return True, "Verified hazard — rerouting recommended"

    return True, "Credible source — rerouting as precaution"


def evaluate_reroute(
    original_request: NavigationRequest,
    current_route: RouteOption,
    incoming_hazard: HazardReport,
    provider: str = "fixture",
) -> tuple[NavigationResponse, str]:
    """
    Evaluate whether to reroute given an incoming hazard report.

    Parameters
    ----------
    original_request : The original NavigationRequest
    current_route    : The route the user is currently on
    incoming_hazard  : New hazard report received
    provider         : Routing provider (fixture / ors / here)

    Returns
    -------
    (NavigationResponse, reroute_reason_or_explanation)
    """
    request_id = str(uuid.uuid4())
    logger.info(
        f"[rerouting] Evaluating hazard: type={incoming_hazard.hazard_type.value} "
        f"source={incoming_hazard.source.value}"
    )

    credible, credibility_reason = _is_hazard_credible(incoming_hazard)

    if not credible:
        # Return existing route without change
        logger.info(f"[rerouting] Hazard REJECTED — {credibility_reason}")
        explanation = (
            f"Rerouting NOT triggered. Hazard rejected: {credibility_reason}. "
            f"Continuing on current route: {current_route.description}"
        )
        return (
            NavigationResponse(
                request_id=request_id,
                routes=[current_route],
                recommended_route_id=current_route.route_id,
                explanation=explanation,
                data_source=current_route.source,
                is_fixture=(current_route.source == DataSource.FIXTURE),
            ),
            explanation,
        )

    # Credible hazard — get fresh routes (avoiding affected route)
    logger.info(f"[rerouting] Credible hazard accepted — {credibility_reason}. Fetching alternatives.")
    new_nav = get_safe_routes(original_request, provider=provider)

    # Filter out current route if possible
    alternatives = [r for r in new_nav.routes if r.route_id != current_route.route_id]
    if not alternatives:
        alternatives = new_nav.routes

    explanation = (
        f"⚠ Rerouting triggered. Reason: {credibility_reason}. "
        f"Hazard: {incoming_hazard.hazard_type.value} — {incoming_hazard.description}. "
        f"New recommended route: {alternatives[0].description if alternatives else 'none found'}."
        + (" [FIXTURE DATA]" if new_nav.is_fixture else "")
    )

    return (
        NavigationResponse(
            request_id=request_id,
            routes=alternatives,
            recommended_route_id=alternatives[0].route_id if alternatives else None,
            explanation=explanation,
            data_source=new_nav.data_source,
            is_fixture=new_nav.is_fixture,
        ),
        explanation,
    )
