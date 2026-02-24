from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class OntologyInstance:
    value: str


@dataclass
class OntologyResource:
    uri: str
    label: str
    # 0 = class, 1 = property (kept close to thesis wording)
    type: int
    instances: List[OntologyInstance] = field(default_factory=list)

    def add_instance(self, v: str) -> None:
        self.instances.append(OntologyInstance(value=v))


@dataclass
class Parameter:
    name: str
    io: str  # 'in' | 'out'
    datatype: Optional[str] = None

    # step 5
    special_type: Optional[str] = None  # 'navigation'|'unknown'|'geospatial'|None

    # step 6/8
    ontology_candidates: List[OntologyResource] = field(default_factory=list)

    # step 7
    suggestions: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)

    # step 9 validation result
    validated: bool = False


@dataclass
class Operation:
    name: str
    method: str = "GET"
    url: str = ""
    inputs: List[Parameter] = field(default_factory=list)
    outputs: List[Parameter] = field(default_factory=list)


@dataclass
class Service:
    kind: str  # 'rest'|'wfs'
    base_url: str
    operations: List[Operation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    executable: bool = True
    notes: List[str] = field(default_factory=list)
