from __future__ import annotations

import hashlib
import json
from typing import Dict, Any, List, Optional

import requests

from ..utils.cache import SqliteCache


class SparqlClient:
    def __init__(self, endpoint_url: str, cache: SqliteCache | None = None, timeout_s: float = 20.0, user_agent: str = "geosws-annotator/0.1.0"):
        self.endpoint_url = endpoint_url
        self.cache = cache
        self.timeout_s = timeout_s
        self.user_agent = user_agent

    def _cache_key(self, query: str) -> str:
        h = hashlib.sha256(query.encode("utf-8")).hexdigest()
        return f"sparql:{self.endpoint_url}:{h}"

    def query(self, sparql: str) -> Dict[str, Any]:
        key = self._cache_key(sparql)
        if self.cache:
            hit = self.cache.get(key)
            if hit is not None:
                return hit.value
        headers = {
            "Accept": "application/sparql-results+json",
            "User-Agent": self.user_agent,
        }
        # DBpedia supports GET with ?query=
        resp = requests.get(self.endpoint_url, params={"query": sparql, "format": "json"}, headers=headers, timeout=self.timeout_s)
        resp.raise_for_status()
        data = resp.json()
        if self.cache:
            self.cache.set(key, data)
        return data

    @staticmethod
    def bindings_to_values(data: Dict[str, Any], var: str) -> List[str]:
        out: List[str] = []
        for row in data.get("results", {}).get("bindings", []):
            if var in row:
                out.append(row[var]["value"])
        return out


def sparql_instances_of_class(class_uri: str, limit: int = 50) -> str:
    # Listing 5.7 in thesis (with LIMIT added)
    return f"SELECT DISTINCT ?val WHERE {{ ?val a <{class_uri}> }} LIMIT {int(limit)}"


def sparql_instances_of_property(prop_uri: str, limit: int = 50) -> str:
    # Listing 5.8 in thesis (with LIMIT added)
    return f"SELECT DISTINCT ?val WHERE {{ ?val <{prop_uri}> ?b }} LIMIT {int(limit)}"


def sparql_all_classes_and_properties(lang: str = "en", limit: Optional[int] = None) -> str:
    # Fetch ontology elements and labels for a local index.
    # Note: endpoints differ; for DBpedia ontology this works reasonably well.
    lim = f"LIMIT {int(limit)}" if limit is not None else ""
    return f"""
SELECT DISTINCT ?uri ?label ?type WHERE {{
  {{
    ?uri a owl:Class .
    OPTIONAL {{ ?uri rdfs:label ?label . FILTER(langMatches(lang(?label), '{lang}')) }}
    BIND('class' AS ?type)
  }}
  UNION
  {{
    ?uri a rdf:Property .
    OPTIONAL {{ ?uri rdfs:label ?label . FILTER(langMatches(lang(?label), '{lang}')) }}
    BIND('property' AS ?type)
  }}
}} {lim}
"""
