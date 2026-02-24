from __future__ import annotations

import re
import unicodedata
from typing import List


_CAMEL_RE = re.compile(r"([a-z0-9])([A-Z])")


def normalize_term(term: str) -> str:
    """Normalize a parameter/label for matching.

    - strip whitespace
    - lowercase
    - remove diacritics
    - collapse separators
    """
    term = term.strip()
    term = unicodedata.normalize("NFKD", term)
    term = "".join(ch for ch in term if not unicodedata.combining(ch))
    term = term.lower()
    term = re.sub(r"[\s\-_/]+", " ", term)
    term = re.sub(r"[^a-z0-9\s]", "", term)
    term = re.sub(r"\s+", " ", term).strip()
    return term


def split_identifier(term: str) -> List[str]:
    """Split camelCase/snake_case/kebab-case identifiers into tokens."""
    t = term.strip()
    t = t.replace("-", " ").replace("_", " ")
    t = _CAMEL_RE.sub(r"\1 \2", t)
    t = re.sub(r"\s+", " ", t).strip()
    tokens = [tok for tok in t.split(" ") if tok]
    return tokens


def delete_special_characters(term: str) -> str:
    # Equivalent to the thesis' idea of removing ',', '-', etc.
    return re.sub(r"[^A-Za-z0-9]+", " ", term).strip()
