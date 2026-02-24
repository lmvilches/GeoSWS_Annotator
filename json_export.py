from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Protocol, Optional
import requests


class SuggestionProvider(Protocol):
    def suggestions(self, term: str, max_results: int = 10) -> List[str]: ...


class SynonymProvider(Protocol):
    def synonyms(self, term: str, max_results: int = 10) -> List[str]: ...


@dataclass
class DatamuseProvider:
    """Uses Datamuse API (free, no key) for suggestions/synonyms-ish.
    - suggestions: /sug
    - synonyms: /words?rel_syn=
    """
    base_url: str = "https://api.datamuse.com"
    timeout_s: float = 15.0

    def suggestions(self, term: str, max_results: int = 10) -> List[str]:
        resp = requests.get(f"{self.base_url}/sug", params={"s": term, "max": max_results}, timeout=self.timeout_s)
        resp.raise_for_status()
        return [x["word"] for x in resp.json() if "word" in x]

    def synonyms(self, term: str, max_results: int = 10) -> List[str]:
        resp = requests.get(f"{self.base_url}/words", params={"rel_syn": term, "max": max_results}, timeout=self.timeout_s)
        resp.raise_for_status()
        return [x["word"] for x in resp.json() if "word" in x]


def build_provider(name: str, settings: Dict[str, Any]) -> Any:
    name = (name or "").strip().lower()
    if name == "datamuse":
        return DatamuseProvider(
            base_url=settings.get("base_url", "https://api.datamuse.com"),
            timeout_s=float(settings.get("timeout_s", 15.0)),
        )
    raise ValueError(f"Unknown provider '{name}'. Supported: datamuse")
