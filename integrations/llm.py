"""
integrations/llm.py — ASI:One / OpenAI-compatible LLM integration.

Used ONLY for:
  - Natural-language interpretation of user requests
  - Generating human-readable explanations of deterministic results
  - Summarising structured outputs

The LLM is NEVER the authority for safety decisions, route recommendations,
or emergency guidance. All critical logic is deterministic Python.
"""
from __future__ import annotations

import logging
from typing import Optional

import config

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    """Lazily initialise the OpenAI-compatible client."""
    global _client
    if _client is not None:
        return _client
    if not config.LLM_AVAILABLE:
        return None
    try:
        from openai import OpenAI
        _client = OpenAI(
            base_url=config.ASI1_BASE_URL,
            api_key=config.ASI1_API_KEY,
        )
        logger.info(f"[llm] ASI:One client initialised (model={config.ASI1_MODEL})")
        return _client
    except ImportError:
        logger.error("[llm] openai package not installed.")
        return None


def explain(
    system_prompt: str,
    user_context: str,
    fallback_text: str,
    max_tokens: int = 400,
) -> str:
    """
    Ask the LLM to generate a natural-language explanation.

    Returns fallback_text if:
      - ASI1_API_KEY not configured
      - Network/API error occurs
      - Response is empty

    Parameters
    ----------
    system_prompt  : Sets the LLM's role and constraints
    user_context   : The structured data to explain (JSON string or plain text)
    fallback_text  : Returned when LLM is unavailable
    max_tokens     : Token budget for the response
    """
    client = _get_client()
    if client is None:
        logger.info("[llm] LLM not available — returning fallback explanation")
        return fallback_text

    try:
        response = client.chat.completions.create(
            model=config.ASI1_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_context},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        text = response.choices[0].message.content or ""
        if not text.strip():
            return fallback_text
        return text.strip()
    except Exception as e:
        logger.warning(f"[llm] LLM call failed: {e}. Returning fallback.")
        return fallback_text


def interpret_intent(user_message: str) -> dict:
    """
    Parse a natural-language user message into a structured intent dict.
    Falls back to a default intent if LLM unavailable.

    Returns
    -------
    dict with keys:
      intent   : str  — one of: navigate, analyse, safe_haven, guardian, emergency,
                                reroute, privacy, unknown
      entities : dict — extracted entities (location, type, etc.)
    """
    client = _get_client()
    if client is None:
        return {"intent": "unknown", "entities": {}, "raw": user_message}

    system = (
        "You are a safety-focused assistant. Parse the user message and return JSON only.\n"
        "Return exactly this structure:\n"
        '{"intent": "<one of: navigate|analyse|safe_haven|guardian|emergency|reroute|privacy|unknown>", '
        '"entities": {"origin": null, "destination": null, "location": null, "type": null}}\n'
        "Do NOT include explanations — return JSON only."
    )
    try:
        response = client.chat.completions.create(
            model=config.ASI1_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
            max_tokens=150,
            temperature=0.0,
        )
        import json
        text = response.choices[0].message.content or "{}"
        # Strip markdown fences if present
        text = text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(text)
    except Exception as e:
        logger.warning(f"[llm] Intent parsing failed: {e}")
        return {"intent": "unknown", "entities": {}, "raw": user_message}
