from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from typing import Any

import requests

from .config import settings

MEMORY_LAYERS = ("short_term", "long_term", "episodic", "semantic")

ROUTER_SYSTEM_PROMPT = """You route a user query to one or more memory sources.
Return JSON only, with this exact shape:
{"layers":["long_term"],"reason":"short explanation"}

Memory sources:
- short_term: information that must be recovered from messages in the current thread.
- long_term: stable user-specific facts, preferences, projects, commitments, or profile.
- episodic: a particular past attempt, incident, outcome, fix, or experience.
- semantic: shared policies, playbooks, rules, procedures, or domain knowledge.

Choose every source required to answer, but no unnecessary source. Do not classify by
tense alone: words such as 'just' or 'soon' do not require short_term unless earlier
messages in the current thread are needed. Return only layer names listed above.
"""


@dataclass(frozen=True)
class RouteDecision:
    layers: list[str]
    reason: str
    source: str
    fallback_used: bool = False
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def route_query(query: str) -> list[str]:
    """Deterministic fallback router retained for offline/error operation."""
    q = query.casefold()
    hints = {
        "short_term": (
            "trong thread", "thread nay", "vua nhac", "tin nhan", "recent",
            "conversation", "hoi thoai", "constraint con hieu luc",
        ),
        "long_term": (
            "minh thich", "toi thich", "ngon ngu minh", "uu tien", "preference",
            "open-loop", "open loop",
            "du an", "backend", "stack", "hoc kieu nao", "project rieng",
            "ten/ma project",
        ),
        "episodic": (
            "lan truoc", "da thu", "trajectory", "reflection", "kinh nghiem",
            "ma su co", "tung xu ly", "tung lam",
        ),
        "semantic": (
            "quy tac", "policy", "payment", "retry", "playbook", "domain", "knowledge",
            "header", "quy trinh", "huong dan chung", "context window", "context cho agent",
            "budget bon tang", "ty le budget", "ty le phan bo", "ma ngan sach",
        ),
    }
    selected = [layer for layer in MEMORY_LAYERS if any(hint in q for hint in hints[layer])]
    if "semantic" in selected and ("khong can policy" in q or "dung policy" in q):
        semantic_positive = ("payment", "retry", "playbook", "budget", "context window")
        if not any(hint in q for hint in semantic_positive):
            selected.remove("semantic")
    return selected or ["long_term", "episodic", "semantic"]


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if not match:
            raise ValueError("Router response did not contain a JSON object")
        value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("Router response must be a JSON object")
    return value


def _validate_layers(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("Router field 'layers' must be a list")
    requested = {str(item).strip() for item in value}
    invalid = requested.difference(MEMORY_LAYERS)
    if invalid:
        raise ValueError(f"Unknown memory layers: {sorted(invalid)}")
    layers = [layer for layer in MEMORY_LAYERS if layer in requested]
    if not layers:
        raise ValueError("Router selected no memory layer")
    return layers


def route_with_llm(query: str, *, timeout: float = 30.0) -> RouteDecision:
    """Route from query alone; use deterministic rules only when the LLM is unavailable."""
    base_url = os.getenv("GEMINI_BASE_URL", "").rstrip("/")
    if not base_url or not settings.gemini_api_key:
        return RouteDecision(
            layers=route_query(query),
            reason="LLM router is not configured; deterministic fallback was used.",
            source="rules",
            fallback_used=True,
            error="Missing GEMINI_BASE_URL or GEMINI_API_KEY",
        )

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.gemini_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.gemini_model,
                "messages": [
                    {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                ],
                "temperature": 0,
                "max_tokens": 250,
            },
            timeout=timeout,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        payload = _extract_json(str(content))
        return RouteDecision(
            layers=_validate_layers(payload.get("layers")),
            reason=str(payload.get("reason") or "No reason supplied").strip(),
            source="llm",
        )
    except Exception as exc:  # noqa: BLE001 - routing must retain an offline path
        return RouteDecision(
            layers=route_query(query),
            reason="LLM routing failed; deterministic fallback was used.",
            source="rules",
            fallback_used=True,
            error=f"{type(exc).__name__}: {exc}",
        )
