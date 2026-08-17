from __future__ import annotations

import json
from typing import Any

from .config import settings
from .context_budget import ContextBudgetManager
from .utils import cap_query, join_nonempty, normalize
from .zep_common import prime_eval_thread, render_graph_search


class StudentMemory:
    """Only this file needs to be edited by students."""

    def __init__(self, client: Any):
        self.client = client
        self.budget = ContextBudgetManager(settings.context_tokens)

    # NOTE: Zep rejects graph.search queries longer than 400 characters. Some
    # eval queries are longer than that, so wrap every query with
    # `cap_query(query)` (see src/utils.py) before passing it to graph.search.

    @staticmethod
    def _render_episodes(
        results: Any,
        *,
        episode_char_cap: int | None = None,
        ignored_roles: set[str] | None = None,
        compact_json: bool = False,
    ) -> str:
        """Render distinct source episodes without retrieval-only query messages."""
        parts: list[str] = []
        seen: set[str] = set()
        ignored = {role.casefold() for role in (ignored_roles or set())}

        for episode in getattr(results, "episodes", None) or []:
            role = str(getattr(episode, "role", "") or "")
            if role.casefold() in ignored:
                continue

            content = str(getattr(episode, "content", "") or "").strip()
            if not content:
                continue

            if compact_json:
                try:
                    payload = json.loads(content)
                except (json.JSONDecodeError, TypeError):
                    payload = None
                if isinstance(payload, dict) and payload.get("summary"):
                    content = str(payload["summary"]).strip()

            key = normalize(content)
            if key in seen:
                continue
            seen.add(key)

            if episode_char_cap:
                content = content[:episode_char_cap]
            parts.append(f"EPISODE: {content}")

        return join_nonempty(parts)

    def retrieve_long_term(self, user_id: str, thread_id: str, query: str) -> str:
        # LAB TODO 1/4
        # 1) prime_eval_thread(...) has already been provided as scaffolding.
        # 2) call thread.get_user_context(thread_id=...)
        # 3) return the .context string.
        # Bonus: append graph.search(scope="edges", limit>=20) facts with
        #        validity ranges (a low limit can miss deadline/open-loop facts).
        prime_eval_thread(self.client, user_id, thread_id, query)
        user_context = self.client.thread.get_user_context(thread_id=thread_id)
        context_block = getattr(user_context, "context", "") or ""

        try:
            facts = self.client.graph.search(
                user_id=user_id,
                query=cap_query(query),
                scope="edges",
                limit=20,
            )
            fact_text = render_graph_search(facts)
        except Exception:
            fact_text = ""

        return join_nonempty([context_block, fact_text], sep="\n\n")

    def retrieve_episodic(self, user_id: str, query: str) -> str:
        # LAB TODO 2/4
        # Use client.graph.search(user_id=..., query=cap_query(query),
        #     scope="episodes", limit=...) then render_graph_search(...).
        # Tip: verbose session episodes can crowd out concise, marker-bearing
        # reflections under the tight episodic budget — render_graph_search
        # accepts an `episode_char_cap` to keep more distinct episodes.
        results = self.client.graph.search(
            user_id=user_id,
            query=cap_query(query),
            scope="episodes",
            # Retrieval-only evaluation messages remain as raw Zep episodes even
            # with ignore_roles. Fetch broadly, then remove them by provenance.
            limit=50,
        )
        return self._render_episodes(
            results,
            episode_char_cap=180,
            ignored_roles={"Evaluation User"},
        )

    def retrieve_semantic(self, graph_id: str, query: str) -> str:
        # LAB TODO 3/4
        # Search the standalone graph (graph_id, NOT user_id).
        # Recommended: scope="episodes" — it returns raw document text that keeps
        # literal markers (e.g. PAYMENT-RULE-3). The "auto" scope returns
        # extracted facts that DROP those literal codes, so avoid it here.
        # Fallback: scope="nodes".
        capped_query = cap_query(query)
        try:
            results = self.client.graph.search(
                graph_id=graph_id,
                query=capped_query,
                scope="episodes",
                limit=8,
            )
        except Exception:
            results = self.client.graph.search(
                graph_id=graph_id,
                query=capped_query,
                scope="nodes",
                limit=8,
            )
        # The KB is ingested as both JSON and text. Collapse JSON to its summary
        # and deduplicate the matching text copy before the semantic budget trim.
        return self._render_episodes(results, compact_json=True)

    def assemble_context(self, layers: dict[str, str]) -> tuple[str, dict[str, dict[str, int]]]:
        # LAB TODO 4/4
        # Use ContextBudgetManager to enforce 10/4/3/3 budget and priority order.
        return self.budget.assemble(layers)
