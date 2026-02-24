from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ..sparql.client import SparqlClient, sparql_all_classes_and_properties
from ..utils.text import normalize_term


@dataclass
class OntologyElement:
    uri: str
    label: str
    type: int  # 0 class, 1 property


class OntologyIndex:
    def __init__(self, elements: List[OntologyElement]):
        self.elements = elements
        # inverted index: normalized label -> list of idx
        self.by_norm_label: Dict[str, List[int]] = {}
        for i, el in enumerate(elements):
            k = normalize_term(el.label) if el.label else normalize_term(el.uri.rsplit('/', 1)[-1])
            self.by_norm_label.setdefault(k, []).append(i)

    @classmethod
    def from_json(cls, path: str) -> "OntologyIndex":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        elements = [OntologyElement(uri=e["uri"], label=e.get("label",""), type=e["type"]) for e in data["elements"]]
        return cls(elements)

    def to_json(self, path: str) -> None:
        data = {"elements": [{"uri": e.uri, "label": e.label, "type": e.type} for e in self.elements]}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def build_from_sparql(cls, client: SparqlClient, languages: List[str] | None = None, limit: Optional[int] = None) -> "OntologyIndex":
        languages = languages or ["en"]
        elements: List[OntologyElement] = []
        seen = set()
        for lang in languages:
            q = sparql_all_classes_and_properties(lang=lang, limit=limit)
            data = client.query("""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            """ + q)
            for row in data.get("results", {}).get("bindings", []):
                uri = row["uri"]["value"]
                label = row.get("label", {}).get("value", "")
                typ = row.get("type", {}).get("value", "class")
                t = 0 if typ == "class" else 1
                key = (uri, label, t)
                if key in seen:
                    continue
                seen.add(key)
                elements.append(OntologyElement(uri=uri, label=label, type=t))
        return cls(elements)
