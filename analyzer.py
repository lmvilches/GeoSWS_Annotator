from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from ..utils.text import normalize_term
from ..utils.similarity import all_scores
from .index import OntologyIndex, OntologyElement


@dataclass(frozen=True)
class MatchResult:
    element: OntologyElement
    score: float
    metric: str  # 'exact'|'jaro'|'jaro_winkler'|'levenshtein_ratio'


class OntologyMatcher:
    def __init__(self, index: OntologyIndex):
        self.index = index

    def match(
        self,
        term: str,
        exact_match: bool = True,
        use_similarity: bool = True,
        jaro_threshold: float = 0.92,
        jaro_winkler_threshold: float = 0.92,
        levenshtein_ratio_threshold: float = 0.85,
        top_k: int = 10,
    ) -> List[MatchResult]:
        term_n = normalize_term(term)
        results: List[MatchResult] = []

        if exact_match and term_n in self.index.by_norm_label:
            for idx in self.index.by_norm_label[term_n]:
                el = self.index.elements[idx]
                results.append(MatchResult(element=el, score=1.0, metric="exact"))

        if use_similarity:
            # brute force over elements (OK for DBpedia ontology scale; for huge ontologies, use ANN/LSH)
            for el in self.index.elements:
                label = el.label or el.uri.rsplit("/", 1)[-1]
                label_n = normalize_term(label)
                scores = all_scores(term_n, label_n)
                if scores.jaro >= jaro_threshold:
                    results.append(MatchResult(el, scores.jaro, "jaro"))
                if scores.jaro_winkler >= jaro_winkler_threshold:
                    results.append(MatchResult(el, scores.jaro_winkler, "jaro_winkler"))
                if scores.levenshtein_ratio >= levenshtein_ratio_threshold:
                    results.append(MatchResult(el, scores.levenshtein_ratio, "levenshtein_ratio"))

        # de-duplicate by element URI, keep best score
        best = {}
        for r in results:
            k = r.element.uri
            if k not in best or r.score > best[k].score:
                best[k] = r

        out = sorted(best.values(), key=lambda r: r.score, reverse=True)
        return out[: max(1, top_k)]
