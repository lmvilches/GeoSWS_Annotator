from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from ..utils.cache import SqliteCache
from ..utils.text import delete_special_characters
from .providers import SuggestionProvider, SynonymProvider


@dataclass
class EnrichmentResult:
    suggestions: List[str]
    synonyms: List[str]


class Enricher:
    """Implements a practical version of the thesis' suggestions/synonyms enrichment.

    Roughly matches the pseudo-code shown as genericAlgorithmSuggSyn / algorithmSuggSyn.
    """

    def __init__(self, sugg: Optional[SuggestionProvider], syn: Optional[SynonymProvider], cache: SqliteCache | None = None):
        self.sugg = sugg
        self.syn = syn
        self.cache = cache

    def enrich(self, term: str, max_suggestions: int = 10, max_synonyms: int = 10) -> EnrichmentResult:
        cache_key = f"enrich:{term}:{max_suggestions}:{max_synonyms}"
        if self.cache:
            hit = self.cache.get(cache_key)
            if hit is not None:
                return EnrichmentResult(suggestions=hit.value.get("suggestions", []), synonyms=hit.value.get("synonyms", []))

        suggestions: List[str] = []
        synonyms: List[str] = []

        # suggestions(term)
        if self.sugg is not None:
            suggestions = self.sugg.suggestions(term, max_results=max_suggestions) or []

        # if no suggestions, delete special characters and try again
        if not suggestions and self.sugg is not None:
            cleaned = delete_special_characters(term)
            if cleaned and cleaned != term:
                suggestions = self.sugg.suggestions(cleaned, max_results=max_suggestions) or []

        # synonyms for each suggestion
        if self.syn is not None:
            for s in suggestions:
                try:
                    syns = self.syn.synonyms(s, max_results=max_synonyms) or []
                except Exception:
                    syns = []
                synonyms.extend(syns)

            # also synonyms(term) itself
            try:
                synonyms.extend(self.syn.synonyms(term, max_results=max_synonyms) or [])
            except Exception:
                pass

        # de-dup & keep order
        def dedup(xs: List[str]) -> List[str]:
            seen = set()
            out = []
            for x in xs:
                k = x.strip().lower()
                if not k or k in seen:
                    continue
                seen.add(k)
                out.append(x.strip())
            return out

        res = EnrichmentResult(suggestions=dedup(suggestions), synonyms=dedup(synonyms))
        if self.cache:
            self.cache.set(cache_key, {"suggestions": res.suggestions, "synonyms": res.synonyms})
        return res
