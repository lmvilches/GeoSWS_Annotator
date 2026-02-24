from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class SparqlEndpointConfig:
    name: str
    url: str
    timeout_s: float = 20.0
    user_agent: str = "geosws-annotator/0.1.0"


@dataclass
class OntologyIndexConfig:
    # If provided, the matcher will use this local JSON index instead of querying SPARQL.
    index_path: Optional[str] = None

    # If building the index, these control what we fetch.
    languages: List[str] = field(default_factory=lambda: ["en"])
    limit_per_type: Optional[int] = None  # None = no LIMIT (can be slow)


@dataclass
class ExternalResourcesConfig:
    enable_suggestions: bool = True
    enable_synonyms: bool = True

    # Provider names are resolved in external/providers.py
    suggestion_provider: str = "datamuse"
    synonym_provider: str = "datamuse"

    # Provider-specific settings (API keys, base URLs, etc.)
    provider_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MatchingConfig:
    exact_match: bool = True
    use_similarity: bool = True

    # Similarity metric thresholds (0..1). You can tune these per experiment.
    jaro_threshold: float = 0.92
    jaro_winkler_threshold: float = 0.92
    levenshtein_ratio_threshold: float = 0.85

    # When multiple candidates exist, keep top-k per term
    top_k: int = 10


@dataclass
class PipelineConfig:
    sparql_endpoints: List[SparqlEndpointConfig]
    ontology_index: OntologyIndexConfig = field(default_factory=OntologyIndexConfig)
    external_resources: ExternalResourcesConfig = field(default_factory=ExternalResourcesConfig)
    matching: MatchingConfig = field(default_factory=MatchingConfig)

    cache_sqlite_path: str = "data/cache.sqlite"

    # Sample sizes for instance retrieval and validation
    instances_limit: int = 50
    validation_trials: int = 20

    # Network
    http_timeout_s: float = 25.0


@dataclass
class WfsTarget:
    base_url: str  # e.g., http://example.com/geoserver/wfs
    version: str = "1.1.0"


@dataclass
class RestTarget:
    url: str  # full URL of operation endpoint
    method: str = "GET"
    # Optional hints: a dict of param->example value(s)
    input_hints: Dict[str, Any] = field(default_factory=dict)


def load_config(path: str) -> Dict[str, Any]:
    import json
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
