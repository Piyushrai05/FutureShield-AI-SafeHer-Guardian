"""
coordinator.py — SafeHer Guardian Coordinator.

Validates inputs, selects the appropriate capability, combines results,
and returns an explainable answer. The LLM is used for NL explanation only —
all safety decisions are deterministic Python functions.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Optional

import config
from models.safety import Location, NavigationRequest, HazardReport, HazardType, DataSource
from models.emergency import EmergencyType, EmergencyRequest
from models.guardian import ConsentType
from models.privacy import PermissionLevel

from capabilities import navigation, safety_analysis, safe_haven, guardian, emergency, rerouting, privacy
from integrations import llm

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are SafeHer Guardian, an AI safety assistant. 
Your role is to explain structured safety information clearly and compassionately.
RULES:
- Never invent route times, distances, or opening hours.
- Never claim emergency services were dispatched unless confirmed.
- Always surface data-source caveats in your explanation.
- Prioritise clarity and calm in emergency situations.
"""


def _build_fallback(data: dict, intent: str) -> str:
    """Build a plain-text fallback explanation when LLM is unavailable."""
    if intent == "navigate":
        routes = data.get("routes", [])
        if routes:
            r = routes[0]
            return (
                f"Route found: {r.get('description', 'N/A')} "
                f"(Safety score: {r.get('safety_score', 'N/A')}/10). "
                f"Note: {r.get('data_caveat', '')}"
            )
        return "No routes found."
    if intent == "emergency":
        return f"CALL {data.get('emergency_number', '112')} NOW. " + " ".join(data.get("guidance", [])[:2])
    return str(data)


def handle_navigate(params: dict) -> dict:
    """Capability 1: Safety-first navigation."""
    origin = Location(
        lat=params.get("origin_lat", 12.9716),
        lon=params.get("origin_lon", 77.5946),
        label=params.get("origin_label", "Current Location"),
    )
    destination = Location(
        lat=params.get("dest_lat", 12.9800),
        lon=params.get("dest_lon", 77.6000),
        label=params.get("dest_label", "Destination"),
    )
    user_id = params.get("user_id", "anonymous")
    req = NavigationRequest(
        origin=origin,
        destination=destination,
        user_id=user_id,
        prefer_safety=params.get("prefer_safety", True),
    )
    result = navigation.get_safe_routes(req, provider=config.ROUTING_PROVIDER)

    routes_data = [r.model_dump() for r in result.routes]
    explanation = llm.explain(
        system_prompt=_SYSTEM_PROMPT,
        user_context=f"Route results (intent=navigate):\n{result.explanation}\nRoutes: {routes_data}",
        fallback_text=result.explanation,
    )
    return {
        "capability": "navigate",
        "request_id": result.request_id,
        "routes": routes_data,
        "recommended_route_id": result.recommended_route_id,
        "is_fixture": result.is_fixture,
        "explanation": explanation,
        "generated_at": result.generated_at.isoformat(),
    }


def handle_analyse(params: dict) -> dict:
    """Capability 2: Safety evidence analysis."""
    loc = Location(
        lat=params.get("lat", 12.9716),
        lon=params.get("lon", 77.5946),
    )
    hazards = []  # In production, fetch from hazard provider
    result = safety_analysis.analyse_safety(
        location=loc,
        hazards=hazards,
        staffed_places_nearby=params.get("staffed_places_nearby", 0),
        emergency_access_confirmed=params.get("emergency_access_confirmed", False),
    )
    result_data = result.model_dump()
    explanation = llm.explain(
        system_prompt=_SYSTEM_PROMPT,
        user_context=f"Safety analysis result:\n{result_data}",
        fallback_text=result.explanation,
    )
    return {
        "capability": "analyse",
        "score": result.overall_score,
        "confidence": result.confidence.value,
        "hazards_count": len(result.hazards_found),
        "missing_data": result.missing_data_items,
        "explanation": explanation,
        "analysed_at": result.analysed_at.isoformat(),
    }


def handle_safe_haven(params: dict) -> dict:
    """Capability 3: Safe haven discovery."""
    loc = Location(
        lat=params.get("lat", 12.9716),
        lon=params.get("lon", 77.5946),
    )
    place_type_str = params.get("place_type")
    place_types = None
    if place_type_str:
        try:
            from models.safety import SafeHaven
            place_types = [SafeHaven.PlaceType(place_type_str)]
        except ValueError:
            pass

    havens = safe_haven.find_safe_havens(
        near=loc,
        place_types=place_types,
        max_results=params.get("max_results", 5),
        provider=config.POI_PROVIDER,
    )
    havens_data = [h.model_dump() for h in havens]
    explanation = llm.explain(
        system_prompt=_SYSTEM_PROMPT,
        user_context=f"Safe haven results:\n{havens_data}",
        fallback_text=f"Found {len(havens)} candidate safe haven(s). Opening hours not verified.",
    )
    return {
        "capability": "safe_haven",
        "count": len(havens),
        "havens": havens_data,
        "explanation": explanation,
    }


def handle_emergency(params: dict) -> dict:
    """Capability 5: Emergency assistance."""
    req = EmergencyRequest(
        request_id=str(uuid.uuid4()),
        user_id=params.get("user_id", "anonymous"),
        emergency_type=EmergencyType(params.get("emergency_type", "general")),
        description=params.get("description", ""),
        country_code=params.get("country_code", "IN"),
    )
    loc = None
    if "lat" in params and "lon" in params:
        loc = Location(lat=params["lat"], lon=params["lon"])

    result = emergency.get_emergency_guidance(req, nearest_location=loc)
    havens_data = [h.model_dump() for h in result.nearest_safe_havens]

    explanation = llm.explain(
        system_prompt=_SYSTEM_PROMPT,
        user_context=(
            f"EMERGENCY GUIDANCE — number={result.emergency_number}\n"
            f"Steps: {result.guidance}\nDispatch: {result.dispatch_note}"
        ),
        fallback_text=f"CALL {result.emergency_number} NOW. " + " ".join(result.guidance[:2]),
    )
    return {
        "capability": "emergency",
        "emergency_number": result.emergency_number,
        "guidance": result.guidance,
        "dispatch_status": result.dispatch_status.value,
        "dispatch_note": result.dispatch_note,
        "nearest_safe_havens": havens_data,
        "explanation": explanation,
        "generated_at": result.generated_at.isoformat(),
    }


def handle_unknown(user_message: str) -> dict:
    """Fallback for unrecognised intents."""
    fallback = (
        "I'm SafeHer Guardian — your personal safety assistant. "
        "I can help with: navigation, safety analysis, safe havens, guardian mode, "
        "emergency assistance, rerouting, and privacy settings. "
        "Please describe what you need help with."
    )
    explanation = llm.explain(
        system_prompt=_SYSTEM_PROMPT,
        user_context=f"User said: {user_message!r}. Respond helpfully about what SafeHer Guardian can do.",
        fallback_text=fallback,
    )
    return {"capability": "unknown", "explanation": explanation}


def process_message(user_message: str, params: Optional[dict] = None) -> dict:
    """
    Main coordinator entry point.

    1. Interpret intent (LLM or keyword fallback)
    2. Validate and dispatch to capability function
    3. Enrich result with LLM explanation
    4. Return structured response

    Parameters
    ----------
    user_message : Raw text from the user/agent
    params       : Optional pre-parsed parameters (bypass intent parsing)
    """
    params = params or {}
    logger.info(f"[coordinator] Processing message: {user_message[:100]!r}")

    # Step 1: Intent interpretation
    intent_result = llm.interpret_intent(user_message)
    intent = intent_result.get("intent", "unknown")
    entities = intent_result.get("entities", {})
    logger.info(f"[coordinator] Intent: {intent} entities: {entities}")

    # Merge LLM-extracted entities with explicit params (explicit wins)
    merged = {**entities, **params}

    # Keyword override for safety when LLM unavailable
    if intent == "unknown":
        msg_lower = user_message.lower()
        if any(w in msg_lower for w in ["route", "navigate", "direction", "way to"]):
            intent = "navigate"
        elif any(w in msg_lower for w in ["emergency", "help", "sos", "danger", "call 112"]):
            intent = "emergency"
        elif any(w in msg_lower for w in ["hospital", "pharmacy", "police", "petrol", "safe place"]):
            intent = "safe_haven"
        elif any(w in msg_lower for w in ["hazard", "safe", "danger score", "risk"]):
            intent = "analyse"

    # Step 2: Dispatch
    try:
        if intent == "navigate":
            return handle_navigate(merged)
        elif intent == "analyse":
            return handle_analyse(merged)
        elif intent == "safe_haven":
            return handle_safe_haven(merged)
        elif intent == "emergency":
            return handle_emergency(merged)
        else:
            return handle_unknown(user_message)
    except Exception as e:
        logger.exception(f"[coordinator] Error processing intent={intent}: {e}")
        return {
            "capability": intent,
            "error": str(e),
            "explanation": f"An error occurred processing your request: {e}",
        }
