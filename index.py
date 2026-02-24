from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


def levenshtein_distance(a: str, b: str) -> int:
    """Classic Levenshtein distance (O(len(a)*len(b)))."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    # ensure a is shorter for memory
    if len(a) > len(b):
        a, b = b, a

    previous = list(range(len(a) + 1))
    for i, bc in enumerate(b, start=1):
        current = [i]
        for j, ac in enumerate(a, start=1):
            insert = current[j - 1] + 1
            delete = previous[j] + 1
            replace = previous[j - 1] + (0 if ac == bc else 1)
            current.append(min(insert, delete, replace))
        previous = current
    return previous[-1]


def levenshtein_ratio(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    dist = levenshtein_distance(a, b)
    return 1.0 - dist / max(len(a), len(b))


def jaro_similarity(s: str, t: str) -> float:
    """Jaro similarity (0..1)."""
    if s == t:
        return 1.0
    s_len = len(s)
    t_len = len(t)
    if s_len == 0 or t_len == 0:
        return 0.0

    match_distance = max(s_len, t_len) // 2 - 1
    s_matches = [False] * s_len
    t_matches = [False] * t_len

    matches = 0
    transpositions = 0

    # count matches
    for i in range(s_len):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, t_len)
        for j in range(start, end):
            if t_matches[j]:
                continue
            if s[i] != t[j]:
                continue
            s_matches[i] = True
            t_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    # count transpositions
    k = 0
    for i in range(s_len):
        if not s_matches[i]:
            continue
        while not t_matches[k]:
            k += 1
        if s[i] != t[k]:
            transpositions += 1
        k += 1

    transpositions //= 2
    return (matches / s_len + matches / t_len + (matches - transpositions) / matches) / 3.0


def jaro_winkler_similarity(s: str, t: str, prefix_scale: float = 0.1, max_prefix: int = 4) -> float:
    j = jaro_similarity(s, t)
    # common prefix up to max_prefix
    prefix = 0
    for sc, tc in zip(s, t):
        if sc == tc:
            prefix += 1
        else:
            break
        if prefix >= max_prefix:
            break
    return j + prefix * prefix_scale * (1.0 - j)


@dataclass(frozen=True)
class SimilarityScores:
    jaro: float
    jaro_winkler: float
    levenshtein_ratio: float


def all_scores(a: str, b: str) -> SimilarityScores:
    return SimilarityScores(
        jaro=jaro_similarity(a, b),
        jaro_winkler=jaro_winkler_similarity(a, b),
        levenshtein_ratio=levenshtein_ratio(a, b),
    )
