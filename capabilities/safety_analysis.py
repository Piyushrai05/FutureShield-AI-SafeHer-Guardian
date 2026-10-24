"""
capabilities/safety_analysis.py — Capability 2: Safety Evidence Analysis.

Evaluates hazards, staffed-place data, emergency access, data-source timestamps,
missing information, and confidence. NEVER equates missing data with safety.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from models.safety import (
    Location,
    HazardReport,
    SafetyAnalysis,
    ConfidenceLevel,
    DataSource,
    HazardType,
)

logger = logging.getLogger(__name__)


def _assess_confidence(
    hazards: list[HazardReport],
    missing_items: list[str],
    has_live_data: bool,
) -> ConfidenceLevel:
    """Determine confidence based on data completeness."""
    if not has_live_data:
        return ConfidenceLevel.LOW
    if missing_items:
        return ConfidenceLevel.LOW if len(missing_items) > 2 else ConfidenceLevel.MEDIUM
    if any(h.is_stale for h in hazards):
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.HIGH


def analyse_safety(
    location: Location,
    hazards: list[HazardReport],
    staffed_places_nearby: int = 0,
    emergency_access_confirmed: bool = False,
    data_source: DataSource = DataSource.FIXTURE,
    data_timestamp: Optional[datetime] = None,
) -> SafetyAnalysis:
    """
    Core safety analysis logic. Deterministic — does not call LLM.

    RULE: Missing data is surfaced as a risk factor, never silently ignored.

    Parameters
    ----------
    location                   : Point being analysed
    hazards                    : Known hazard reports for this area/route
    staffed_places_nearby      : Count of known staffed places within ~500m
    emergency_access_confirmed : Whether 112/emergency access is verified
    data_source                : Where the data came from
    data_timestamp             : When the data was last refreshed (None = unknown)

    Returns
    -------
    SafetyAnalysis with score, confidence, hazards, and missing-data list.
    """
    missing_data: list[str] = []

    # Check for critical missing information
    if data_timestamp is None:
        missing_data.append("data_timestamp: unknown — cannot assess staleness")

    if staffed_places_nearby == 0:
        missing_data.append("staffed_places_nearby: no data — cannot confirm safe refuge access")

    if not emergency_access_confirmed:
        missing_data.append("emergency_access: not confirmed for this location")

    if data_source == DataSource.FIXTURE:
        missing_data.append("live_data: provider not configured — analysis based on fixtures only")

    # Base score starts at 10 and deductions are applied
    score = 10.0

    # Deduct for hazards
    for hazard in hazards:
        if hazard.verified:
            score -= 2.0
        else:
            score -= 0.8  # Unverified still carries risk
        if hazard.is_stale:
            score -= 0.2  # Stale data adds uncertainty

    # Deduct for missing critical items
    score -= len(missing_data) * 0.5

    # Boost slightly if staffed places and emergency access known
    if staffed_places_nearby > 0:
        score = min(10.0, score + 0.5 * min(staffed_places_nearby, 3))

    if emergency_access_confirmed:
        score = min(10.0, score + 1.0)

    score = max(0.0, round(score, 2))

    confidence = _assess_confidence(
        hazards=hazards,
        missing_items=missing_data,
        has_live_data=(data_source == DataSource.LIVE_API),
    )

    explanation_parts = [
        f"Safety score: {score}/10 (confidence: {confidence.value}).",
    ]
    if missing_data:
        explanation_parts.append(
            "⚠ Missing data (absence does NOT imply safety): "
            + "; ".join(missing_data)
        )
    if hazards:
        verified = [h for h in hazards if h.verified]
        unverified = [h for h in hazards if not h.verified]
        explanation_parts.append(
            f"Hazards: {len(verified)} verified, {len(unverified)} unverified."
        )
    if data_source == DataSource.FIXTURE:
        explanation_parts.append(
            "[FIXTURE] Analysis uses test data — not a live safety assessment."
        )

    return SafetyAnalysis(
        overall_score=score,
        confidence=confidence,
        hazards_found=hazards,
        missing_data_items=missing_data,
        explanation=" ".join(explanation_parts),
    )
